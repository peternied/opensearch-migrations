package org.opensearch.migrations.bulkload.lucene.version_7;

import java.io.IOException;
import java.nio.file.Path;

import org.opensearch.migrations.bulkload.lucene.LuceneDirectoryReader;
import org.opensearch.migrations.bulkload.lucene.LuceneIndexReader;
import org.opensearch.migrations.bulkload.lucene.ReaderUtils;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import shadow.lucene7.org.apache.lucene.index.DirectoryReader;
import shadow.lucene7.org.apache.lucene.index.SoftDeletesDirectoryReaderWrapper;
import shadow.lucene7.org.apache.lucene.store.FSDirectory;

@AllArgsConstructor
@Slf4j
public class IndexReader7 implements LuceneIndexReader {

    protected final Path indexDirectoryPath;
    protected final boolean softDeletesPossible;
    protected final String softDeletesField;

    public LuceneDirectoryReader getReader(String segmentsFileName) throws IOException {
        try {
            // Use the utility class with fallback approach to handle codec errors
            var reader = ReaderUtils.openReaderWithFallback7(indexDirectoryPath, segmentsFileName);
            
            // Apply soft deletes wrapper if needed
            if (softDeletesPossible) {
                reader = new SoftDeletesDirectoryReaderWrapper(reader, softDeletesField);
            }
            
            return new DirectoryReader7(reader, indexDirectoryPath);
        } catch (IOException e) {
            log.error("Failed to open index with segments file {}: {}", segmentsFileName, e.getMessage());
            throw e;
        }
    }
}
