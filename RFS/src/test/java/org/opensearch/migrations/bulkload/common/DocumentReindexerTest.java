package org.opensearch.migrations.bulkload.common;

import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;

import org.opensearch.migrations.bulkload.tracing.IRfsContexts;
import org.opensearch.migrations.bulkload.worker.WorkItemCursor;
import org.opensearch.migrations.reindexer.tracing.IDocumentMigrationContexts;
import org.opensearch.migrations.transform.IJsonTransformer;
import org.opensearch.migrations.transform.TransformationLoader;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import reactor.core.Disposable;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Scheduler;
import reactor.core.scheduler.Schedulers;
import reactor.test.StepVerifier;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

@Slf4j
class DocumentReindexerTest {

    private static final int MAX_DOCS_PER_BULK = 3;
    private static final int MAX_BYTES_PER_BULK_REQUEST = 1024*1024;
    private static final int MAX_CONCURRENT_REQUESTS = 1;

    @Mock
    private OpenSearchClient mockClient;

    @Mock
    private IDocumentMigrationContexts.IDocumentReindexContext mockContext;

    private DocumentReindexer documentReindexer;

    @BeforeEach
    void setUp() {
        MockitoAnnotations.openMocks(this);
        documentReindexer = new DocumentReindexer(mockClient, MAX_DOCS_PER_BULK, MAX_BYTES_PER_BULK_REQUEST, MAX_CONCURRENT_REQUESTS, null);
        when(mockContext.createBulkRequest()).thenReturn(mock(IRfsContexts.IRequestContext.class));
    }

    @Test
    void reindex_shouldBufferByDocumentCount() {
        Flux<RfsLuceneDocument> documentStream = Flux.range(1, 10)
            .map(i -> createTestDocument(i));

        when(mockClient.sendBulkRequest(eq("test-index"), any(), any()))
            .thenAnswer(invocation -> {
                List<?> bulkBody = invocation.getArgument(1);
                long docCount = bulkBody.size();
                return Mono.just(new OpenSearchClient.BulkResponse(200, "OK", null,
                    String.format("{\"took\":1,\"errors\":false,\"items\":[%s]}", "{}".repeat((int)docCount))));
            });

        StepVerifier.create(documentReindexer.reindex("test-index",  documentStream, mockContext))
            .expectNextCount(3)
            .expectNext(new WorkItemCursor(10))
            .thenRequest(4)
            .verifyComplete();

        int expectedBulkRequests = (10 + MAX_DOCS_PER_BULK - 1) / MAX_DOCS_PER_BULK;
        verify(mockClient, times(expectedBulkRequests)).sendBulkRequest(eq("test-index"), any(), any());

        @SuppressWarnings("unchecked")
        var bulkRequestCaptor = ArgumentCaptor.forClass((Class<List<BulkDocSection>>)(Class<?>) List.class);
        verify(mockClient, times(expectedBulkRequests)).sendBulkRequest(eq("test-index"), bulkRequestCaptor.capture(), any());

        var capturedBulkRequests = bulkRequestCaptor.getAllValues();
        assertEquals(expectedBulkRequests, capturedBulkRequests.size());

        for (int i = 0; i < expectedBulkRequests - 1; i++) {
            assertEquals(MAX_DOCS_PER_BULK, capturedBulkRequests.get(i).size());
        }

        var lastRequest = capturedBulkRequests.get(expectedBulkRequests - 1);
        int remainingDocs = 10 % MAX_DOCS_PER_BULK;
        assertEquals(remainingDocs, lastRequest.size());
    }

    @Test
    void reindex_shouldBufferBySize() {
        int numDocs = 5;
        Flux<RfsLuceneDocument> documentStream = Flux.range(1, numDocs)
            .map(i -> createLargeTestDocument(i, MAX_BYTES_PER_BULK_REQUEST / 2 + 1));

        when(mockClient.sendBulkRequest(eq("test-index"), any(), any()))
            .thenAnswer(invocation -> {
                List<?> bulkBody = invocation.getArgument(1);
                long docCount = bulkBody.size();
                return Mono.just(new OpenSearchClient.BulkResponse(200, "OK", null,
                    String.format("{\"took\":1,\"errors\":false,\"items\":[%s]}", "{}".repeat((int)docCount))));
            });

        StepVerifier.create(documentReindexer.reindex("test-index", documentStream, mockContext))
        .expectNextCount(4)
        .expectNext(new WorkItemCursor(5))
        .thenRequest(5)
        .verifyComplete();

        verify(mockClient, times(numDocs)).sendBulkRequest(eq("test-index"), any(), any());

        @SuppressWarnings("unchecked")
        var bulkRequestCaptor = ArgumentCaptor.forClass((Class<List<BulkDocSection>>)(Class<?>) List.class);
        verify(mockClient, times(numDocs)).sendBulkRequest(eq("test-index"), bulkRequestCaptor.capture(), any());

        var capturedBulkRequests = bulkRequestCaptor.getAllValues();
        assertEquals(numDocs, capturedBulkRequests.size());

        for (var bulkDocSections : capturedBulkRequests) {
            assertEquals(1, bulkDocSections.size());
        }
    }

    @Test
    void reindex_shouldBufferByTransformedSize() throws JsonProcessingException {
        // Set up the transformer that replaces the sourceDoc from the document
        var replacedSourceDoc = Map.of("simpleKey", "simpleValue");
        IJsonTransformer transformer = originalJsons -> {
            ((List<Map<String, Object>>) originalJsons)
                    .forEach(json -> json.put("source", replacedSourceDoc));
            return originalJsons;
        };
        int numDocs = 5;

        // Initialize DocumentReindexer with the transformer
        documentReindexer = new DocumentReindexer(
            mockClient, numDocs, MAX_BYTES_PER_BULK_REQUEST, MAX_CONCURRENT_REQUESTS, () -> transformer
        );

        Flux<RfsLuceneDocument> documentStream = Flux.range(1, numDocs)
            .map(i -> createLargeTestDocument(i, MAX_BYTES_PER_BULK_REQUEST / 2 + 1)
        );

        when(mockClient.sendBulkRequest(eq("test-index"), any(), any()))
            .thenAnswer(invocation -> {
                List<?> bulkBody = invocation.getArgument(1);
                long docCount = bulkBody.size();
                return Mono.just(new OpenSearchClient.BulkResponse(200, "OK", null,
                    String.format("{\"took\":1,\"errors\":false,\"items\":[%s]}", "{}".repeat((int)docCount))));
            });

        StepVerifier.create(documentReindexer.reindex("test-index", documentStream, mockContext))
            .expectNext(new WorkItemCursor(1))
            .thenRequest(5)
            .verifyComplete();

        // Verify that only one bulk request was sent
        verify(mockClient, times(1)).sendBulkRequest(eq("test-index"), any(), any());

        // Capture the bulk request to verify its contents
        @SuppressWarnings("unchecked")
        var bulkRequestCaptor = ArgumentCaptor.forClass(
            (Class<List<BulkDocSection>>)(Class<?>) List.class
        );
        verify(mockClient).sendBulkRequest(eq("test-index"), bulkRequestCaptor.capture(), any());

        var capturedBulkRequests = bulkRequestCaptor.getValue();
        assertEquals(numDocs, capturedBulkRequests.size(),
            "All documents should be in a single bulk request after transformation");
        assertTrue(BulkDocSection.convertToBulkRequestBody(capturedBulkRequests).contains(
                new ObjectMapper().writeValueAsString(replacedSourceDoc)));
    }

    @Test
    void reindex_shouldSendDocumentsLargerThanMaxBulkSize() {
        Flux<RfsLuceneDocument> documentStream = Flux.just(createLargeTestDocument(1, MAX_BYTES_PER_BULK_REQUEST * 3 / 2));

        when(mockClient.sendBulkRequest(eq("test-index"), any(), any()))
            .thenAnswer(invocation -> {
                List<?> bulkBody = invocation.getArgument(1);
                long docCount = bulkBody.size();
                return Mono.just(new OpenSearchClient.BulkResponse(200, "OK", null,
                    String.format("{\"took\":1,\"errors\":false,\"items\":[%s]}", "{}".repeat((int)docCount))));
            });

        StepVerifier.create(documentReindexer.reindex("test-index", documentStream, mockContext))
            .expectNext(new WorkItemCursor(1))
            .thenRequest(1)
            .verifyComplete();

        verify(mockClient, times(1)).sendBulkRequest(eq("test-index"), any(), any());

        @SuppressWarnings("unchecked")
        var bulkRequestCaptor = ArgumentCaptor.forClass((Class<List<BulkDocSection>>)(Class<?>) List.class);
        verify(mockClient).sendBulkRequest(eq("test-index"), bulkRequestCaptor.capture(), any());

        var capturedBulkRequests = bulkRequestCaptor.getValue();
        assertTrue(capturedBulkRequests.get(0).asBulkIndexString().getBytes(StandardCharsets.UTF_8).length > MAX_BYTES_PER_BULK_REQUEST, "Bulk request should be larger than max bulk size");
        assertEquals(1, capturedBulkRequests.size(), "Should contain 1 document");
    }

    @Test
    void reindex_shouldTrimAndRemoveNewlineFromSource() {
        Flux<RfsLuceneDocument> documentStream = Flux.just(createTestDocumentWithWhitespace(1));

        when(mockClient.sendBulkRequest(eq("test-index"), any(), any()))
            .thenAnswer(invocation -> {
                List<?> bulkBody = invocation.getArgument(1);
                long docCount = bulkBody.size();
                return Mono.just(new OpenSearchClient.BulkResponse(200, "OK", null,
                    String.format("{\"took\":1,\"errors\":false,\"items\":[%s]}", "{}".repeat((int)docCount))));
            });

        StepVerifier.create(documentReindexer.reindex("test-index", documentStream, mockContext))
            .expectNext(new WorkItemCursor(1))
            .thenRequest(1)
            .verifyComplete();

        verify(mockClient, times(1)).sendBulkRequest(eq("test-index"), any(), any());

        @SuppressWarnings("unchecked")
        var bulkRequestCaptor = ArgumentCaptor.forClass((Class<List<BulkDocSection>>)(Class<?>) List.class);
        verify(mockClient).sendBulkRequest(eq("test-index"), bulkRequestCaptor.capture(), any());

        var capturedBulkRequests = bulkRequestCaptor.getValue();
        assertEquals(1, capturedBulkRequests.size(), "Should contain 1 document");
        assertEquals("{\"index\":{\"_id\":\"1\",\"_index\":\"test-index\"}}\n{\"field\":\"value\"}", capturedBulkRequests.get(0).asBulkIndexString());    }

    @Test
    void reindex_shouldRespectMaxConcurrentRequests() {
        int numDocs = 100;
        int maxConcurrentRequests = 5;
        DocumentReindexer concurrentReindexer = new DocumentReindexer(mockClient, 1, MAX_BYTES_PER_BULK_REQUEST, maxConcurrentRequests, null);

        Flux<RfsLuceneDocument> documentStream = Flux.range(1, numDocs).map(i -> createTestDocument(i));

        AtomicInteger concurrentRequests = new AtomicInteger(0);
        AtomicInteger maxObservedConcurrency = new AtomicInteger(0);

        when(mockClient.sendBulkRequest(eq("test-index"), any(), any()))
            .thenAnswer(invocation -> {
                int current = concurrentRequests.incrementAndGet();
                maxObservedConcurrency.updateAndGet(max -> Math.max(max, current));
                return Mono.just(new OpenSearchClient.BulkResponse(200, "OK", null, "{\"took\":1,\"errors\":false,\"items\":[{}]}"))
                    .delayElement(Duration.ofMillis(100))
                    .doOnTerminate(concurrentRequests::decrementAndGet);
            });

        StepVerifier.create(concurrentReindexer.reindex("test-index", documentStream, mockContext))
            .expectNextCount(99)
            .expectNext(new WorkItemCursor(100))
            .thenRequest(100)
            .verifyComplete();

        verify(mockClient, times(numDocs)).sendBulkRequest(eq("test-index"), any(), any());
        assertTrue(maxObservedConcurrency.get() <= maxConcurrentRequests,
            "Max observed concurrency (" + maxObservedConcurrency.get() +
            ") should not exceed max concurrent requests (" + maxConcurrentRequests + ")");
    }

    @Test
    void reindex_shouldTransformDocuments() {
        // Define the transformation configuration
        final String CONFIG = "[" +
                "  {" +
                "    \"JsonTransformerForDocumentTypeRemovalProvider\":\"\"" +
                "  }" +
                "]";

        // Initialize the transformer using the provided configuration
        IJsonTransformer transformer = new TransformationLoader().getTransformerFactoryLoader(CONFIG);

        // Initialize DocumentReindexer with the transformer
        documentReindexer = new DocumentReindexer(mockClient, MAX_DOCS_PER_BULK, MAX_BYTES_PER_BULK_REQUEST, MAX_CONCURRENT_REQUESTS, () -> transformer);

        // Create a stream of documents, some requiring transformation and some not
        Flux<RfsLuceneDocument> documentStream = Flux.just(
                createTestDocumentWithType(1, "_type1"),
                createTestDocumentWithType(2, null),
                createTestDocumentWithType(3, "_type3")
        );

        // Mock the client to capture the bulk requests
        when(mockClient.sendBulkRequest(eq("test-index"), any(), any()))
                .thenAnswer(invocation -> {
                    List<?> bulkBody = invocation.getArgument(1);
                    return Mono.just(new OpenSearchClient.BulkResponse(200, "OK", null,
                            String.format("{\"took\":1,\"errors\":false,\"items\":[%s]}",
                                    "{}".repeat(bulkBody.size()))));
                });

        // Execute the reindexing process
        StepVerifier.create(documentReindexer.reindex("test-index", documentStream, mockContext))
            .expectNext(new WorkItemCursor(1))
            .thenRequest(1)
            .verifyComplete();

        // Capture the bulk requests sent to the mock client
        @SuppressWarnings("unchecked")
        var bulkRequestCaptor = ArgumentCaptor.forClass((Class<List<BulkDocSection>>)(Class<?>) List.class);
        verify(mockClient, times(1)).sendBulkRequest(eq("test-index"), bulkRequestCaptor.capture(), any());

        var capturedBulkRequests = bulkRequestCaptor.getValue();
        assertEquals(3, capturedBulkRequests.size(), "Should contain 3 transformed documents");

        // Verify that the transformation was applied correctly
        BulkDocSection transformedDoc1 = capturedBulkRequests.get(0);
        BulkDocSection transformedDoc2 = capturedBulkRequests.get(1);
        BulkDocSection transformedDoc3 = capturedBulkRequests.get(2);

        assertEquals("{\"index\":{\"_id\":\"1\",\"_index\":\"test-index\"}}\n{\"field\":\"value\"}", transformedDoc1.asBulkIndexString(),
                "Document 1 should have _type removed");
        assertEquals("{\"index\":{\"_id\":\"2\",\"_index\":\"test-index\"}}\n{\"field\":\"value\"}", transformedDoc2.asBulkIndexString(),
                "Document 2 should remain unchanged as _type is not defined");
        assertEquals("{\"index\":{\"_id\":\"3\",\"_index\":\"test-index\"}}\n{\"field\":\"value\"}", transformedDoc3.asBulkIndexString(),
                "Document 3 should have _type removed");
    }

    private RfsLuceneDocument createTestDocument(int id) {
        return new RfsLuceneDocument(id, String.valueOf(id), null, "{\"field\":\"value\"}", null);
    }

    private RfsLuceneDocument createTestDocumentWithWhitespace(int id) {
        return new RfsLuceneDocument(id, String.valueOf(id), null, " \r\n\t{\"field\"\n:\"value\"}\r\n\t ", null);
    }

    private RfsLuceneDocument createLargeTestDocument(int id, int size) {
        String largeField = "x".repeat(size);
        return new RfsLuceneDocument(id, String.valueOf(id), null, "{\"field\":\"" + largeField + "\"}", null);
    }

    /**
     * Helper method to create a test document with a specific _type.
     *
     * @param id The document ID.
     * @param type The _type of the document.
     * @return A new instance of RfsLuceneDocument with the specified _type.
     */
    private RfsLuceneDocument createTestDocumentWithType(int id, String type) {
        String source = "{\"field\":\"value\"}";
        return new RfsLuceneDocument(id, String.valueOf(id), type, source, null);
    }

    /**
     * Tests that scheduler disposal during batch processing is handled gracefully.
     * Simulates a race condition where the scheduler becomes unavailable while processing documents.
     */
    @Test
    void reindex_shouldHandleSchedulerDisposalGracefully() {
        var numDocs = 2;
        var documentStream = Flux.range(1, numDocs)
            .map(this::createTestDocument);

        when(mockClient.sendBulkRequest(eq("test-index"), any(), any()))
            .thenReturn(Mono.just(new OpenSearchClient.BulkResponse(200, "OK", null, 
                "{\"took\":1,\"errors\":false,\"items\":[{}]}")));

        // Allow more scheduler calls before rejection to ensure both docs are processed
        var testReindexer = createReindexerWithDisposingScheduler(10);

        StepVerifier.create(testReindexer.reindex("test-index", documentStream, mockContext))
            .expectError(RejectedExecutionException.class)
            .verify();

        // When scheduler fails immediately, no bulk requests should be made
        verify(mockClient, times(0)).sendBulkRequest(eq("test-index"), any(), any());
    }

    /**
     * Tests that concurrent requests handle scheduler disposal during subscribeOn operations.
     * Focuses on the specific race condition in sendBulkRequest's subscribeOn call.
     */
    @Test 
    void reindex_shouldHandleRejectionDuringSubscribeOn() {
        var numDocs = 1;
        var documentStream = Flux.just(createTestDocument(1));

        when(mockClient.sendBulkRequest(eq("test-index"), any(), any()))
            .thenReturn(Mono.just(new OpenSearchClient.BulkResponse(200, "OK", null, 
                "{\"took\":1,\"errors\":false,\"items\":[{}]}")));

        var testReindexer = createReindexerWithSubscribeOnRejection();

        StepVerifier.create(testReindexer.reindex("test-index", documentStream, mockContext))
            .expectError(RejectedExecutionException.class)
            .verify();

        verify(mockClient, times(1)).sendBulkRequest(eq("test-index"), any(), any());
    }

    private DocumentReindexer createReindexerWithDisposingScheduler(int maxCallsBeforeRejection) {
        return new DocumentReindexer(
            mockClient, 1, MAX_BYTES_PER_BULK_REQUEST, MAX_CONCURRENT_REQUESTS, null
        ) {
            @Override
            Flux<WorkItemCursor> reindexDocsInParallelBatches(
                Flux<RfsDocument> docs, 
                String indexName, 
                IDocumentMigrationContexts.IDocumentReindexContext context) {
                
                var mockScheduler = createDisposingScheduler(maxCallsBeforeRejection);
                var bulkDocsBatches = batchDocsBySizeOrCount(docs);
                
                return bulkDocsBatches
                    .publishOn(mockScheduler, 1)
                    .flatMapSequential(docsGroup -> 
                        sendBulkRequest(UUID.randomUUID(), docsGroup, indexName, context, mockScheduler),
                        MAX_CONCURRENT_REQUESTS)
                    .doFinally(signalType -> mockScheduler.dispose());
            }
        };
    }

    private DocumentReindexer createReindexerWithSubscribeOnRejection() {
        return new DocumentReindexer(
            mockClient, 1, MAX_BYTES_PER_BULK_REQUEST, MAX_CONCURRENT_REQUESTS, null
        ) {
            @Override
            Mono<WorkItemCursor> sendBulkRequest(
                UUID batchId, 
                List<RfsDocument> docsBatch, 
                String indexName, 
                IDocumentMigrationContexts.IDocumentReindexContext context, 
                Scheduler scheduler) {
                
                var rejectionScheduler = createRejectionOnFirstCallScheduler();
                var lastDoc = docsBatch.get(docsBatch.size() - 1);
                var bulkDocSections = docsBatch.stream()
                    .map(rfsDocument -> rfsDocument.document)
                    .collect(Collectors.toList());
                
                return mockClient.sendBulkRequest(indexName, bulkDocSections, context.createBulkRequest())
                    .onErrorResume(e -> Mono.empty())
                    .then(Mono.just(new WorkItemCursor(lastDoc.progressCheckpointNum))
                        .subscribeOn(rejectionScheduler));
            }
        };
    }

    private Scheduler createDisposingScheduler(int maxCallsBeforeRejection) {
        var callCount = new AtomicInteger(0);
        
        return new Scheduler() {
            @Override
            public Disposable schedule(Runnable task) {
                // Always throw immediately to ensure error propagation
                throw new RejectedExecutionException("Scheduler disposed - task rejected");
            }
            
            @Override
            public Disposable schedule(Runnable task, long delay, TimeUnit unit) {
                return schedule(task);
            }
            
            @Override
            public Scheduler.Worker createWorker() {
                return new Scheduler.Worker() {
                    @Override
                    public Disposable schedule(Runnable task) {
                        // Always throw immediately to ensure error propagation
                        throw new RejectedExecutionException("Scheduler disposed - task rejected");
                    }
                    
                    @Override
                    public void dispose() {}
                    
                    @Override
                    public boolean isDisposed() { return true; }
                };
            }
            
            @Override
            public void dispose() {}
            
            @Override
            public boolean isDisposed() { return true; }
        };
    }

    private Scheduler createRejectionOnFirstCallScheduler() {
        return new Scheduler() {
            @Override
            public Disposable schedule(Runnable task) {
                throw new RejectedExecutionException("Scheduler disposed during subscribeOn");
            }
            
            @Override
            public Disposable schedule(Runnable task, long delay, TimeUnit unit) {
                return schedule(task);
            }
            
            @Override
            public Scheduler.Worker createWorker() {
                return new Scheduler.Worker() {
                    @Override
                    public Disposable schedule(Runnable task) {
                        return createRejectionOnFirstCallScheduler().schedule(task);
                    }
                    
                    @Override
                    public void dispose() {}
                    
                    @Override
                    public boolean isDisposed() { return false; }
                };
            }
            
            @Override
            public void dispose() {}
            
            @Override
            public boolean isDisposed() { return false; }
        };
    }
}
