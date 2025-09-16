package org.opensearch.migrations.bulkload.lucene.version_9;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import lombok.extern.slf4j.Slf4j;
import shadow.lucene9.org.apache.lucene.codecs.Codec;

/**
 * A provider for dynamic codec fallbacks that handles unknown codecs encountered
 * during index reading without requiring explicit registration for each one.
 */
@Slf4j
public class DynamicCodecProvider {
    
    // Cache of dynamically created codecs
    private static final Map<String, Codec> dynamicCodecs = new ConcurrentHashMap<>();
    
    // Lucene codec names by major version (for best compatibility)
    private static final Map<Integer, String> DEFAULT_CODEC_BY_VERSION = Map.of(
        5, "Lucene54",
        6, "Lucene62",
        7, "Lucene70",
        8, "Lucene87",
        9, "Lucene94"
    );
    
    // Private constructor to prevent instantiation
    private DynamicCodecProvider() {
        // Utility class, no instantiation
    }
    
    /**
     * Gets a codec by name, creating a dynamic fallback if the codec is not found.
     * 
     * @param name The codec name
     * @return The codec instance (either existing or dynamically created)
     */
    public static Codec getCodec(String name) {
        try {
            // First try to get the standard codec
            return Codec.forName(name);
        } catch (IllegalArgumentException e) {
            if (isCodecNotFoundError(e)) {
                // If not found, check our dynamic registry or create a new one
                return dynamicCodecs.computeIfAbsent(name, DynamicCodecProvider::createDynamicCodec);
            }
            // For other types of exceptions, just propagate
            throw e;
        }
    }
    
    /**
     * Creates a dynamic fallback codec for the given name.
     * 
     * @param codecName The codec name to create a fallback for
     * @return A newly created dynamic fallback codec
     */
    private static Codec createDynamicCodec(String codecName) {
        log.info("Creating dynamic fallback for codec: {}", codecName);
        
        // Try to determine the best base codec to use based on the codec name
        String baseCodecName = determineBaseCodecName(codecName);
        
        // Create and return the dynamic codec
        return new DynamicFallbackCodec(codecName, baseCodecName);
    }
    
    /**
     * Tries to determine the most appropriate base codec to use for a fallback based on the codec name.
     * 
     * @param codecName The name of the codec
     * @return The name of the base codec to use
     */
    private static String determineBaseCodecName(String codecName) {
        // Try to extract version from codec name
        int luceneVersion = tryExtractLuceneVersion(codecName);
        
        if (luceneVersion > 0) {
            // If we could extract a version, use the corresponding default
            return DEFAULT_CODEC_BY_VERSION.getOrDefault(luceneVersion, "Lucene94");
        }
        
        // If name contains "Elasticsearch" or starts with "ES", assume it's an ES codec
        if (codecName.contains("Elasticsearch") || codecName.startsWith("ES")) {
            // ES 7.x typically uses Lucene8x
            if (codecName.contains("7")) {
                return "Lucene87";
            }
            // ES 8.x typically uses Lucene9x
            else if (codecName.contains("8")) {
                return "Lucene94";
            }
        }
        
        // KNN codecs typically use Lucene9x in OpenSearch
        if (codecName.contains("KNN")) {
            return "Lucene94";
        }
        
        // Default to latest known codec
        return "Lucene94";
    }
    
    /**
     * Tries to extract a Lucene major version number from a codec name.
     * 
     * @param codecName The codec name
     * @return The extracted version number, or 0 if none could be extracted
     */
    private static int tryExtractLuceneVersion(String codecName) {
        // Handle standard Lucene codec names like "Lucene94"
        if (codecName.startsWith("Lucene") && codecName.length() >= 7) {
            try {
                // Extract the first digit after "Lucene"
                char versionChar = codecName.charAt(6);
                if (Character.isDigit(versionChar)) {
                    return Character.getNumericValue(versionChar);
                }
            } catch (IndexOutOfBoundsException e) {
                // Ignore and return 0
            }
        }
        return 0;
    }
    
    /**
     * Checks if an exception indicates that a codec was not found.
     * 
     * @param e The exception to check
     * @return true if the exception indicates a codec was not found
     */
    private static boolean isCodecNotFoundError(Exception e) {
        return e.getMessage() != null && 
               e.getMessage().contains("An SPI class of type") && 
               e.getMessage().contains("Codec");
    }
}
