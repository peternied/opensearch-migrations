package org.opensearch.migrations.bulkload.lucene.version_6;

import java.io.IOException;
import java.nio.file.Path;

import org.opensearch.migrations.bulkload.lucene.LuceneDirectoryReader;
import org.opensearch.migrations.bulkload.lucene.LuceneIndexReader;
import org.opensearch.migrations.bulkload.lucene.ReaderUtils;

import lombok.AllArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import shadow.lucene6.org.apache.lucene.index.DirectoryReader;
import shadow.lucene6.org.apache.lucene.store.FSDirectory;

@AllArgsConstructor
@Slf4j
public class IndexReader6 implements LuceneIndexReader {

    protected final Path indexDirectoryPath;

    public LuceneDirectoryReader getReader(String segmentsFileName) throws IOException {
        try {
            // Use the utility class with fallback approach to handle codec errors
            var reader = ReaderUtils.openReaderWithFallback6(indexDirectoryPath, segmentsFileName);
            
            return new DirectoryReader6(reader, indexDirectoryPath);
        } catch (IOException e) {
            log.error("Failed to open index with segments file {}: {}", segmentsFileName, e.getMessage());
            throw e;
        }
    }
}
