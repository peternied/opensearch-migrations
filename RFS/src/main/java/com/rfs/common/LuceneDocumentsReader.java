package com.rfs.common;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Objects;
import java.util.function.Function;

import org.apache.lucene.document.Document;
import org.apache.lucene.index.DirectoryReader;
import org.apache.lucene.index.IndexReader;
import org.apache.lucene.index.SoftDeletesDirectoryReaderWrapper;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.util.BytesRef;

import lombok.Lombok;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Scheduler;
import reactor.core.scheduler.Schedulers;
import reactor.util.function.Tuples;

@RequiredArgsConstructor
@Slf4j
public class LuceneDocumentsReader {
    public static Function<Path, LuceneDocumentsReader> getFactory(boolean softDeletesPossible, String softDeletesField) {
        return path -> new LuceneDocumentsReader(path, softDeletesPossible, softDeletesField);
    }

    protected final Path indexDirectoryPath;
    protected final boolean softDeletesPossible;
    protected final String softDeletesField;

    /**
     * There are a variety of states the documents in our Lucene Index can be in; this method extracts those documents
     * that would be considered "live" from the ElasticSearch/OpenSearch perspective.
     *
     * For context, when ElasticSearch/OpenSearch deletes a document, it doesn't actually remove it from the Lucene Index.
     * Instead, what happens is that the document is marked as "deleted" in the Lucene Index, but it is still present in the
     * Lucene segment on disk.  The next time that segment is merged, the deleted documents are removed from the Lucene Index.
     * A similar thing happens when a document is updated; the old document is marked as "deleted" and a new document is
     * added in a new Lucene segment.  This means that from an ES/OS perspective, you could have a single document that has
     * been created, deleted, recreated, updated, etc. multiple times and only a single version of the doc would exist when
     * you queried the ES/OS Index - but every single iteration of that doc might still exist in the Lucene Segments on disk,
     * all of which have the same _id (from the ES/OS perspective).
     *
     * Additionally, Elasticsearch 7 introduced a feature called "soft deletes" which allows you to mark a document as
     * "deleted" in the Lucene Index without actually removing it from the Lucene Index.  This works by having the
     * application writing the Lucene Index define a field that is used to mark a document as "soft deleted" or not.  When
     * a document is marked as "soft deleted", it is not returned in search results, but it is still present in the Lucene
     * Index.  The status of whether any given document is "soft deleted" or not is stored in the Lucene Index itself.  By
     * default, Elasticsearch 7+ Indices have soft deletes enabled; this is an Index-level setting.
     *
     * In order to retrieve only those documents that would be considered "live" in ES/OS, we use a few tricks:
     * 1. We make sure we use the latest Lucene commit point on the Lucene Index.  A commit is a Lucene abstraction that
     *     comprises a consistent, point-in-time view of the Segments in the Lucene Index.  By default, a DirectoryReader
     *     will use the latest commit point.
     * 2. We use a concept called "liveDocs" to determine if a document is "live" or not.  The liveDocs are a bitset that
     *    is associated with each Lucene segment that tells us if a document is "live" or not.  If a document is hard-deleted
     *    (i.e. deleted from the ES/OS perspective or an old version of an updated doc), then the liveDocs bit for that
     *    document will be false.
     * 3. We wrap our DirectoryReader in a SoftDeletesDirectoryReaderWrapper if it's possible that soft deletes will be
     *    present in the Lucene Index.  This wrapper will filter out documents that are marked as "soft deleted" in the
     *    Lucene Index.

    */
    public Flux<Document> readDocuments() {
        // Create elastic scheduler for i/o bound lucene document reading
        int luceneReaderThreadCount = Schedulers.DEFAULT_BOUNDED_ELASTIC_SIZE;
        Scheduler luceneReaderScheduler = Schedulers.newBoundedElastic(luceneReaderThreadCount, Integer.MAX_VALUE, "luceneReaderScheduler");

        return Flux.using(() -> wrapReader(DirectoryReader.open(FSDirectory.open(indexDirectoryPath)), softDeletesPossible, softDeletesField), reader -> {
            log.atInfo().log(reader.maxDoc() + " documents found in the current Lucene index");

            return Flux.fromIterable(reader.leaves()) // Iterate over each segment
                .flatMap(leafReaderContext -> {
                        var leafReader = leafReaderContext.reader();
                        var liveDocs = leafReader.getLiveDocs();
                        return Flux.range(0, leafReader.maxDoc())
                            .filter(docIdx -> liveDocs == null || liveDocs.get(docIdx)) // Filter for live docs
                            .map(liveDocIdx -> Tuples.of(leafReader, liveDocIdx)); // Build a Tuple2<LeafReader, Integer>
                    }
                )
                .parallel(luceneReaderThreadCount)
                .runOn(luceneReaderScheduler)
                .map(tuple -> getDocument(tuple.getT1(), tuple.getT2(), true)) // Retrieve the document
                .filter(Objects::nonNull) // Skip malformed docs
                .sequential() // Merge parallel streams
                .doFinally(unused -> luceneReaderScheduler.dispose());
        }, reader -> { // Close the DirectoryReader when done
            try {
                reader.close();
            } catch (IOException e) {
                log.atError().setMessage("Failed to close DirectoryReader").setCause(e).log();
                throw Lombok.sneakyThrow(e);
            }
        });
    }

    protected DirectoryReader wrapReader(DirectoryReader reader, boolean softDeletesEnabled, String softDeletesField) throws IOException {
        if (softDeletesEnabled) {
            return new SoftDeletesDirectoryReaderWrapper(reader, softDeletesField);
        }
        return reader;
    }

    protected Document getDocument(IndexReader reader, int docId, boolean isLive) {
        try {
            Document document = reader.document(docId);
            BytesRef sourceBytes = document.getBinaryValue("_source");
            String id;
            try {
                id = Uid.decodeId(document.getBinaryValue("_id").bytes);
                log.atDebug().setMessage("Reading document {}").addArgument(id).log();
            } catch (Exception e) {
                StringBuilder errorMessage = new StringBuilder();
                errorMessage.append("Unable to parse Document id from Document.  The Document's Fields: ");
                document.getFields().forEach(f -> errorMessage.append(f.name()).append(", "));
                log.atError().setMessage(errorMessage.toString()).setCause(e).log();
                return null; // Skip documents with missing id
            }

            if (!isLive) {
                log.atDebug().setMessage("Document {} is not live").addArgument(id).log();
                return null; // Skip these
            }

            if (sourceBytes == null || sourceBytes.bytes.length == 0) {
                log.atWarn().setMessage("Document {} doesn't have the _source field enabled").addArgument(id).log();
                return null;  // Skip these
            }

            log.atDebug().setMessage("Document {} read successfully").addArgument(id).log();
            return document;
        } catch (Exception e) {
            log.atError().setMessage("Failed to read document at Lucene index location {}").addArgument(docId).setCause(e).log();
            return null;
        }
    }
}
