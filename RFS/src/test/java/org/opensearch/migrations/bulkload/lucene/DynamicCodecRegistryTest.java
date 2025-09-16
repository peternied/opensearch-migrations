package org.opensearch.migrations.bulkload.lucene;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import org.junit.Test;
import org.opensearch.migrations.bulkload.lucene.version_9.DynamicCodecProvider;
import org.opensearch.migrations.bulkload.lucene.version_9.DynamicCodecRegistry;
import shadow.lucene9.org.apache.lucene.codecs.Codec;

/**
 * Tests for the dynamic codec registry mechanism.
 */
public class DynamicCodecRegistryTest {

    /**
     * Tests that the dynamic codec registry can be initialized.
     */
    @Test
    public void testRegistryInitialization() {
        boolean result = DynamicCodecRegistry.initialize();
        assertTrue("Dynamic codec registry should initialize successfully", result);
        assertTrue("Dynamic codec registry should be initialized", DynamicCodecRegistry.isInitialized());
    }

    /**
     * Tests that the dynamic codec provider can create fallbacks for unknown codecs.
     */
    @Test
    public void testDynamicCodecProvider() {
        // First ensure registry is initialized
        DynamicCodecRegistry.initialize();
        
        // Try to get a standard codec - should work normally
        Codec standardCodec = DynamicCodecProvider.getCodec("Lucene94");
        assertNotNull("Standard codec should be available", standardCodec);
        
        // Try to get a non-existent codec - should create a dynamic fallback
        String fakeCodecName = "NonExistentCodec" + System.currentTimeMillis();
        Codec dynamicCodec = DynamicCodecProvider.getCodec(fakeCodecName);
        assertNotNull("Dynamic fallback codec should be created for unknown codec", dynamicCodec);
        assertTrue("Dynamic fallback codec should have the requested name", 
                dynamicCodec.getName().equals(fakeCodecName));
    }

    /**
     * Tests that the codec registry can properly handle codec requests after initialization.
     */
    @Test
    public void testCodecLookupAfterRegistryInitialization() {
        // First ensure registry is initialized
        DynamicCodecRegistry.initialize();
        
        // Try to get a non-existent codec directly through the Codec class
        // This should now use our dynamic provider under the hood
        String fakeCodecName = "AnotherNonExistentCodec" + System.currentTimeMillis();
        
        try {
            Codec dynamicCodec = Codec.forName(fakeCodecName);
            assertNotNull("Should be able to get dynamic codec through standard Codec.forName()", dynamicCodec);
            assertTrue("Dynamic codec should have the requested name", 
                    dynamicCodec.getName().equals(fakeCodecName));
        } catch (IllegalArgumentException e) {
            // If this fails, our registry override isn't working properly
            throw new AssertionError("Dynamic codec registry not working correctly: " + e.getMessage(), e);
        }
    }
}
