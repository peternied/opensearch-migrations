package org.opensearch.migrations.bulkload.lucene.version_9;

import java.io.IOException;
import java.nio.file.Path;

import org.opensearch.migrations.bulkload.lucene.LuceneDirectoryReader;
import org.opensearch.migrations.bulkload.lucene.LuceneIndexReader;
import org.opensearch.migrations.bulkload.lucene.ReaderUtils;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import shadow.lucene9.org.apache.lucene.index.DirectoryReader;
import shadow.lucene9.org.apache.lucene.index.SoftDeletesDirectoryReaderWrapper;
import shadow.lucene9.org.apache.lucene.store.FSDirectory;

@AllArgsConstructor
@Slf4j
public class IndexReader9 implements LuceneIndexReader {

    protected final Path indexDirectoryPath;
    protected final boolean softDeletesPossible;
    protected final String softDeletesField;

    public LuceneDirectoryReader getReader(String segmentsFileName) throws IOException {
        try {
            // Use our utility method to open the reader with fallback handling for codec errors
            var reader = ReaderUtils.openReaderWithFallback(indexDirectoryPath, segmentsFileName);
            
            // Apply soft deletes wrapper if needed
            if (softDeletesPossible) {
                reader = new SoftDeletesDirectoryReaderWrapper(reader, softDeletesField);
            }
            
            return new DirectoryReader9(reader, indexDirectoryPath);
        } catch (IOException e) {
            log.error("Failed to open index with segments file {}: {}", segmentsFileName, e.getMessage());
            throw e;
        }
    }
}
