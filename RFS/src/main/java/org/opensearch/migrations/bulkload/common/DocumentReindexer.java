package org.opensearch.migrations.bulkload.common;

import java.util.List;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Predicate;
import java.util.function.Supplier;
import java.util.stream.Collectors;

import org.opensearch.migrations.bulkload.worker.WorkItemCursor;
import org.opensearch.migrations.reindexer.tracing.IDocumentMigrationContexts.IDocumentReindexContext;
import org.opensearch.migrations.transform.IJsonTransformer;
import org.opensearch.migrations.transform.NoopTransformerProvider;
import org.opensearch.migrations.transform.ThreadSafeTransformerWrapper;

import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Scheduler;
import reactor.core.scheduler.Schedulers;
import reactor.util.function.Tuple2;
import reactor.util.function.Tuples;

@Slf4j
public class DocumentReindexer {
    private static final Supplier<IJsonTransformer> NOOP_TRANSFORMER_SUPPLIER = () -> new NoopTransformerProvider().createTransformer(null);

    protected final OpenSearchClient client;
    private final int maxDocsPerBulkRequest;
    private final long maxBytesPerBulkRequest;
    private final int maxConcurrentWorkItems;
    private final ThreadSafeTransformerWrapper threadSafeTransformer;
    private final boolean isNoopTransformer;

    public DocumentReindexer(OpenSearchClient client,
               int maxDocsPerBulkRequest,
               long maxBytesPerBulkRequest,
               int maxConcurrentWorkItems,
               Supplier<IJsonTransformer> transformerSupplier) {
        this.client = client;
        this.maxDocsPerBulkRequest = maxDocsPerBulkRequest;
        this.maxBytesPerBulkRequest = maxBytesPerBulkRequest;
        this.maxConcurrentWorkItems = maxConcurrentWorkItems;
        this.isNoopTransformer = transformerSupplier == null;
        this.threadSafeTransformer = new ThreadSafeTransformerWrapper((this.isNoopTransformer) ? NOOP_TRANSFORMER_SUPPLIER : transformerSupplier);
    }

    public Flux<WorkItemCursor> reindex(
            String indexName,
            Flux<RfsLuceneDocument> documentStream,
            IDocumentReindexContext context) {
    
        int parallelism = Runtime.getRuntime().availableProcessors();
        int batchSize    = Math.min(100, maxDocsPerBulkRequest);
    
        return Flux.using(
            // 1) Resource factory: create executor + scheduler
            () -> {
                var id = new AtomicInteger();
                var executor = Executors.newFixedThreadPool(parallelism, r -> {
                    int threadNum = id.incrementAndGet();
                    return new Thread(() -> {
                        try {
                            r.run();
                        } finally {
                            threadSafeTransformer.close();
                        }
                    }, "DocumentBulkAggregator-" + threadNum);
                });
                var scheduler = Schedulers.fromExecutor(executor);
                return Tuples.of(executor, scheduler);
            },
            // 2) Flux factory: use that scheduler for the entire pipeline
            tuple -> {
                var scheduler = tuple.getT2();
                var flux = documentStream
                    .publishOn(scheduler, 1)
                    .buffer(batchSize)
                    .concatMapIterable(batch -> transformDocumentBatch(threadSafeTransformer, batch, indexName));
    
                return reindexDocsInParallelBatches(flux, indexName, context);
            },
            // 3) Cleanup: dispose scheduler and shut down executor once the Flux completes/errors/cancels
            tuple -> {
                tuple.getT2().dispose();
                tuple.getT1().shutdown();
            }
        );
    }

    Flux<WorkItemCursor> reindexDocsInParallelBatches(Flux<RfsDocument> docs, String indexName, IDocumentReindexContext context) {
        // Use parallel scheduler for send subscription due on non-blocking io client
        var scheduler = Schedulers.newParallel("DocumentBatchReindexer");
        var bulkDocsBatches = batchDocsBySizeOrCount(docs);
        var bulkDocsToBuffer = 50; // Arbitrary, takes up 500MB at default settings

        return bulkDocsBatches
            .limitRate(bulkDocsToBuffer, 1) // Bulk Doc Buffer, Keep Full
            .publishOn(scheduler, 1) // Switch scheduler
            .flatMapSequential(docsGroup -> sendBulkRequest(UUID.randomUUID(), docsGroup, indexName, context, scheduler),
                maxConcurrentWorkItems)
            .doFinally(s -> scheduler.dispose())
            // Allow threading/scheduler exceptions to propagate as they indicate serious issues
            .onErrorResume(e -> {
                if (e instanceof RejectedExecutionException) {
                    return Flux.error(e);
                }
                return Flux.empty();
            });
    }

    @SneakyThrows
    List<RfsDocument> transformDocumentBatch(IJsonTransformer transformer, List<RfsLuceneDocument> docs, String indexName) {
        var originalDocs = docs.stream().map(doc ->
                        RfsDocument.fromLuceneDocument(doc, indexName))
                .collect(Collectors.toList());
        if (!isNoopTransformer) {
            return RfsDocument.transform(transformer, originalDocs);
        }
        return originalDocs;
    }

    /*
     * TODO: Update the reindexing code to rely on _index field embedded in each doc section rather than requiring it in the
     * REST path.  See: https://opensearch.atlassian.net/browse/MIGRATIONS-2232
     */
    Mono<WorkItemCursor> sendBulkRequest(UUID batchId, List<RfsDocument> docsBatch, String indexName, IDocumentReindexContext context, Scheduler scheduler) {
        var lastDoc = docsBatch.get(docsBatch.size() - 1);
        log.atInfo().setMessage("Last doc is: Source Index " + indexName + " Lucene Doc Number " + lastDoc.progressCheckpointNum).log();

        List<BulkDocSection> bulkDocSections = docsBatch.stream()
                .map(rfsDocument -> rfsDocument.document)
                .collect(Collectors.toList());

        return client.sendBulkRequest(indexName, bulkDocSections, context.createBulkRequest()) // Send the request
            .doFirst(() -> log.atInfo().setMessage("Batch Id:{}, {} documents in current bulk request.")
                .addArgument(batchId)
                .addArgument(docsBatch::size)
                .log())
            .doOnSuccess(unused -> log.atDebug().setMessage("Batch Id:{}, succeeded").addArgument(batchId).log())
            .doOnError(error -> log.atError().setMessage("Batch Id:{}, failed {}")
                .addArgument(batchId)
                .addArgument(error::getMessage)
                .log())
            // Prevent recoverable errors from stopping the entire stream, retries occurring within sendBulkRequest
            .onErrorResume(e -> Mono.empty())
            .then(Mono.just(new WorkItemCursor(lastDoc.progressCheckpointNum))
                .subscribeOn(scheduler))
            // Apply error handling to the entire chain including subscribeOn
            .onErrorResume(e -> {
                if (e instanceof RejectedExecutionException) {
                    return Mono.error(e);
                }
                return Mono.empty();
            });
    }

    Flux<List<RfsDocument>> batchDocsBySizeOrCount(Flux<RfsDocument> docs) {
        return docs.bufferUntil(new Predicate<>() {
            private int currentItemCount = 0;
            private long currentSize = 0;

            @Override
            public boolean test(RfsDocument next) {
                // Add one for newline between bulk sections
                var nextSize = next.document.getSerializedLength() + 1L;
                currentSize += nextSize;
                currentItemCount++;

                if (currentItemCount > maxDocsPerBulkRequest || currentSize > maxBytesPerBulkRequest) {
                    // Reset and return true to signal to stop buffering.
                    // Current item is included in the current buffer
                    currentItemCount = 1;
                    currentSize = nextSize;
                    return true;
                }
                return false;
            }
        }, true);
    }

}
