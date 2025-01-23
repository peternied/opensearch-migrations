package org.opensearch.migrations.lucene7;

import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.index.IndexUpgrader;
import org.apache.lucene.index.IndexFormatTooNewException;
import org.apache.lucene.index.IndexFormatTooOldException;
import org.apache.lucene.index.CorruptIndexException;
import org.apache.lucene.util.InfoStream;
import org.apache.lucene.analysis.standard.StandardAnalyzer;
import org.apache.lucene.index.IndexWriterConfig;

import java.io.File;
import java.io.IOException;
import java.nio.file.Paths;

public class Lucene7Upgrader {

    public void upgradeIndex(String indexPath) throws IOException {
        try (FSDirectory dir = FSDirectory.open(Paths.get(indexPath))) {
            var analyzer = new StandardAnalyzer();
            var config = new IndexWriterConfig(analyzer);
            config.setInfoStream(System.out);
            var upgrader = new IndexUpgrader(
                dir, 
                config,
                false
            );
            upgrader.upgrade();
        } catch (Exception e) {
            System.out.println("Lucene7 issue: " + e.getClass().getSimpleName() + ", " + e.getMessage());
        } finally {
            var lockFile = new File(indexPath, "write.lock");
            if (lockFile.exists()) {
                lockFile.delete();
            }
        }
    }
}