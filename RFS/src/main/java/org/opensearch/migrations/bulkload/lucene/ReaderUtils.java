package org.opensearch.migrations.bulkload.lucene;

import java.io.IOException;
import java.nio.file.Path;

import lombok.extern.slf4j.Slf4j;
import org.opensearch.migrations.bulkload.lucene.version_9.DynamicCodecRegistry;
import shadow.lucene9.org.apache.lucene.index.DirectoryReader;
import shadow.lucene9.org.apache.lucene.index.IndexCommit;
import shadow.lucene9.org.apache.lucene.index.IndexFormatTooOldException;
import shadow.lucene9.org.apache.lucene.index.IndexNotFoundException;
import shadow.lucene9.org.apache.lucene.store.FSDirectory;

/**
 * Utility class for opening Lucene readers with fallback mechanisms for handling codec errors.
 */
@Slf4j
public class ReaderUtils {
    
    private ReaderUtils() {
        // Utility class, no instantiation
    }
    
    // Initialize the dynamic codec registry when the class is loaded
    static {
        boolean initialized = DynamicCodecRegistry.initialize();
        if (initialized) {
            log.info("Dynamic codec registry initialized successfully");
        } else {
            log.warn("Failed to initialize dynamic codec registry - fallback codecs will not be available");
        }
    }
    
    /**
     * Opens a DirectoryReader, automatically handling codec errors with dynamic fallbacks.
     * 
     * @param commit The index commit to open
     * @return A DirectoryReader for the index
     * @throws IOException If the index could not be opened
     * @throws IndexFormatTooOldException If the index is too old
     * @throws IndexNotFoundException If the index doesn't exist
     */
    public static DirectoryReader openReaderWithFallback(IndexCommit commit) throws IOException {
        try {
            // With the dynamic codec registry initialized, this should handle unknown codecs
            return DirectoryReader.open(commit);
        } catch (IllegalArgumentException e) {
            if (isCodecError(e)) {
                String missingCodecName = extractMissingCodecName(e.getMessage());
                
                // Check if the dynamic registry is initialized
                if (!DynamicCodecRegistry.isInitialized()) {
                    log.warn("Codec error encountered for codec: {}. Dynamic codec registry is not initialized.", 
                             missingCodecName);
                    throw new IOException("Unable to open index due to missing codec: " + missingCodecName +
                                         ". Dynamic codec registry initialization failed.", e);
                } else {
                    // This should not happen if dynamic registry is working correctly
                    log.error("Codec error still encountered despite dynamic registry for codec: {}", missingCodecName);
                    throw new IOException("Unable to open index. Dynamic codec handling failed for: " + missingCodecName, e);
                }
            }
            throw e;
        }
    }
    
    /**
     * Opens a directory reader for the given path and segments file.
     * 
     * @param indexPath Path to the index directory
     * @param segmentsFileName Segments file name
     * @return DirectoryReader instance
     * @throws IOException If an I/O error occurs
     */
    public static DirectoryReader openReaderWithFallback(Path indexPath, String segmentsFileName) throws IOException {
        try (FSDirectory directory = FSDirectory.open(indexPath)) {
            var commits = DirectoryReader.listCommits(directory);
            var relevantCommit = commits.stream()
                .filter(commit -> segmentsFileName.equals(commit.getSegmentsFileName()))
                .findAny()
                .orElseThrow(() -> new IOException("No such commit with segments file: " + segmentsFileName));
            
            return openReaderWithFallback(relevantCommit);
        }
    }
    
    /**
     * Opens a DirectoryReader for Lucene 7 with fallback handling for codec errors.
     *
     * @param indexPath Path to the index directory
     * @param segmentsFileName Segments file name
     * @return DirectoryReader instance for Lucene 7
     * @throws IOException If an I/O error occurs
     */
    public static shadow.lucene7.org.apache.lucene.index.DirectoryReader openReaderWithFallback7(Path indexPath, String segmentsFileName) throws IOException {
        try (shadow.lucene7.org.apache.lucene.store.FSDirectory directory = shadow.lucene7.org.apache.lucene.store.FSDirectory.open(indexPath)) {
            var commits = shadow.lucene7.org.apache.lucene.index.DirectoryReader.listCommits(directory);
            var relevantCommit = commits.stream()
                .filter(commit -> segmentsFileName.equals(commit.getSegmentsFileName()))
                .findAny()
                .orElseThrow(() -> new IOException("No such commit with segments file: " + segmentsFileName));
            
            try {
                return shadow.lucene7.org.apache.lucene.index.DirectoryReader.open(relevantCommit);
            } catch (IllegalArgumentException e) {
                if (isCodecError(e)) {
                    String missingCodecName = extractMissingCodecName(e.getMessage());
                    log.warn("Codec error encountered for codec: {} when opening Lucene 7 index", missingCodecName);
                    throw new IOException("Unable to open index due to missing codec: " + missingCodecName, e);
                }
                throw e;
            }
        }
    }
    
    /**
     * Opens a DirectoryReader for Lucene 6 with fallback handling for codec errors.
     *
     * @param indexPath Path to the index directory
     * @param segmentsFileName Segments file name
     * @return DirectoryReader instance for Lucene 6
     * @throws IOException If an I/O error occurs
     */
    public static shadow.lucene6.org.apache.lucene.index.DirectoryReader openReaderWithFallback6(Path indexPath, String segmentsFileName) throws IOException {
        try (shadow.lucene6.org.apache.lucene.store.FSDirectory directory = shadow.lucene6.org.apache.lucene.store.FSDirectory.open(indexPath)) {
            var commits = shadow.lucene6.org.apache.lucene.index.DirectoryReader.listCommits(directory);
            var relevantCommit = commits.stream()
                .filter(commit -> segmentsFileName.equals(commit.getSegmentsFileName()))
                .findAny()
                .orElseThrow(() -> new IOException("No such commit with segments file: " + segmentsFileName));
            
            try {
                return shadow.lucene6.org.apache.lucene.index.DirectoryReader.open(relevantCommit);
            } catch (IllegalArgumentException e) {
                if (isCodecError(e)) {
                    String missingCodecName = extractMissingCodecName(e.getMessage());
                    log.warn("Codec error encountered for codec: {} when opening Lucene 6 index", missingCodecName);
                    throw new IOException("Unable to open index due to missing codec: " + missingCodecName, e);
                }
                throw e;
            }
        }
    }
    
    /**
     * Opens a DirectoryReader for Lucene 5 with fallback handling for codec errors.
     *
     * @param indexPath Path to the index directory
     * @param segmentsFileName Segments file name
     * @return DirectoryReader instance for Lucene 5
     * @throws IOException If an I/O error occurs
     */
    public static shadow.lucene5.org.apache.lucene.index.DirectoryReader openReaderWithFallback5(Path indexPath, String segmentsFileName) throws IOException {
        try (shadow.lucene5.org.apache.lucene.store.FSDirectory directory = shadow.lucene5.org.apache.lucene.store.FSDirectory.open(indexPath)) {
            var commits = shadow.lucene5.org.apache.lucene.index.DirectoryReader.listCommits(directory);
            var relevantCommit = commits.stream()
                .filter(commit -> segmentsFileName.equals(commit.getSegmentsFileName()))
                .findAny()
                .orElseThrow(() -> new IOException("No such commit with segments file: " + segmentsFileName));
            
            try {
                return shadow.lucene5.org.apache.lucene.index.DirectoryReader.open(relevantCommit);
            } catch (IllegalArgumentException e) {
                if (isCodecError(e)) {
                    String missingCodecName = extractMissingCodecName(e.getMessage());
                    log.warn("Codec error encountered for codec: {} when opening Lucene 5 index", missingCodecName);
                    throw new IOException("Unable to open index due to missing codec: " + missingCodecName, e);
                }
                throw e;
            }
        }
    }

    /**
     * Extracts the name of the missing codec from an error message.
     * 
     * @param errorMessage The error message to parse
     * @return The codec name, or "Unknown" if it couldn't be extracted
     */
    private static String extractMissingCodecName(String errorMessage) {
        if (errorMessage == null) {
            return "Unknown";
        }
        
        // Error message format: "An SPI class of type shadow.lucene9.org.apache.lucene.codecs.Codec with name 'KNN87Codec' does not exist."
        int startQuote = errorMessage.indexOf("'");
        int endQuote = errorMessage.indexOf("'", startQuote + 1);
        
        if (startQuote >= 0 && endQuote > startQuote) {
            return errorMessage.substring(startQuote + 1, endQuote);
        }
        return "Unknown";
    }
    
    /**
     * Determines if an exception is related to a missing codec.
     * 
     * @param e The exception to check
     * @return true if the exception is related to a missing codec
     */
    private static boolean isCodecError(Exception e) {
        return e.getMessage() != null && 
               e.getMessage().contains("An SPI class of type") && 
               e.getMessage().contains("Codec");
    }
}
