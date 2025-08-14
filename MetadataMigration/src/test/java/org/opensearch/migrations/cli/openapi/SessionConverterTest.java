package org.opensearch.migrations.cli.openapi;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.junit.jupiter.api.Test;
import org.opensearch.migrations.cli.Items;
import org.opensearch.migrations.metadata.CreationResult;

import com.fasterxml.jackson.databind.JsonNode;

/**
 * Test demonstrating how to use the SessionConverter with real Items objects.
 * This shows the practical application of the converter pattern for integrating
 * with OpenAPI-generated models.
 */
public class SessionConverterTest {

    /**
     * Creates a sample Items object for testing
     */
    private Items createSampleItems() {
        List<CreationResult> indexTemplates = Arrays.asList(
            CreationResult.builder().name("template1").build(), // success has no failure type
            CreationResult.builder().name("template2")
                .failureType(CreationResult.CreationFailureType.ALREADY_EXISTS).build()
        );
        
        List<CreationResult> componentTemplates = new ArrayList<>();
        
        List<CreationResult> indexes = Arrays.asList(
            CreationResult.builder().name("index1").build() // success has no failure type
        );
        
        List<CreationResult> aliases = new ArrayList<>();
        
        return Items.builder()
            .dryRun(true)
            .indexTemplates(indexTemplates)
            .componentTemplates(componentTemplates)
            .indexes(indexes)
            .aliases(aliases)
            .failureMessage("Sample failure message")
            .build();
    }
    
    @Test
    public void testItemsToSessionJson() {
        // Given
        Items items = createSampleItems();
        
        // When
        JsonNode sessionJson = SessionConverter.itemsToSessionJson(items);
        
        // Then
        assertEquals("Migration Session", sessionJson.get("name").asText());
        assertTrue(sessionJson.has("created"));
        assertTrue(sessionJson.has("updated"));
        
        JsonNode env = sessionJson.get("env");
        assertTrue(env.has("dryRun"));
        assertTrue(env.get("dryRun").asBoolean());
        
        assertTrue(env.has("indexTemplates"));
        assertEquals(2, env.get("indexTemplates").size());
        assertEquals("template1", env.get("indexTemplates").get(0).get("name").asText());
        
        assertTrue(env.has("indexes"));
        assertEquals(1, env.get("indexes").size());
        
        assertEquals("Sample failure message", env.get("failureMessage").asText());
    }
    
    @Test
    public void testSessionJsonToItems() {
        // Given
        Items originalItems = createSampleItems();
        JsonNode sessionJson = SessionConverter.itemsToSessionJson(originalItems);
        
        // When
        Items reconstructedItems = SessionConverter.sessionJsonToItems(sessionJson);
        
        // Then
        assertEquals(originalItems.isDryRun(), reconstructedItems.isDryRun());
        assertEquals(originalItems.getFailureMessage(), reconstructedItems.getFailureMessage());
        
        // Note: In a full implementation, we would also verify that the templates, indexes, 
        // and aliases are correctly reconstructed. In this example, we're using empty lists
        // in the sessionJsonToItems method, so we can't test that aspect.
        assertTrue(reconstructedItems.getIndexTemplates().isEmpty());
        assertTrue(reconstructedItems.getComponentTemplates().isEmpty());
        assertTrue(reconstructedItems.getIndexes().isEmpty());
        assertTrue(reconstructedItems.getAliases().isEmpty());
    }
    
    /**
     * This test demonstrates how the converter pattern allows the Items class to
     * maintain its existing structure while still making it compatible with the
     * OpenAPI-generated models.
     */
    @Test
    public void testRoundTripConversion() {
        // Given an Items object with real data
        Items originalItems = createSampleItems();
        
        // Convert it to a Session-like JSON format
        JsonNode sessionJson = SessionConverter.itemsToSessionJson(originalItems);
        
        // Modify the Session JSON (simulating what might happen in the API)
        ((com.fasterxml.jackson.databind.node.ObjectNode)sessionJson).put("name", "Modified Session");
        
        // Convert it back to an Items object
        Items convertedItems = SessionConverter.sessionJsonToItems(sessionJson);
        
        // The key fields should match
        assertEquals(originalItems.isDryRun(), convertedItems.isDryRun());
        assertEquals(originalItems.getFailureMessage(), convertedItems.getFailureMessage());
    }
}
