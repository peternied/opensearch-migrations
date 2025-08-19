package org.opensearch.migrations.bulkload.workcoordination;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.opensearch.migrations.bulkload.common.RestClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

/**
 * HTTP client for communicating with the console_link backfill work coordination API.
 */
public class ConsoleApiClient {
    private static final Logger logger = LoggerFactory.getLogger(ConsoleApiClient.class);
    
    private final String baseUrl;
    private final String sessionName;
    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    
    public ConsoleApiClient(String baseUrl, String sessionName) {
        this.baseUrl = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        this.sessionName = sessionName;
        this.httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
        this.objectMapper = new ObjectMapper();
    }
    
    /**
     * Create a new work item.
     */
    public JsonNode createWorkItem(String workItemId, String indexName, int shardNumber, 
                                  int documentCount, long totalSizeBytes) throws IOException, InterruptedException {
        String url = String.format("%s/sessions/%s/backfill/work-items/", baseUrl, sessionName);
        
        String requestBody = String.format("""
            {
                "work_item_id": "%s",
                "index_name": "%s",
                "shard_number": %d,
                "document_count": %d,
                "total_size_bytes": %d
            }
            """, workItemId, indexName, shardNumber, documentCount, totalSizeBytes);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();
        
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 201) {
            throw new IOException("Failed to create work item. Status: " + response.statusCode() + ", Body: " + response.body());
        }
        
        return objectMapper.readTree(response.body());
    }
    
    /**
     * Acquire the next available work item for a worker.
     */
    public JsonNode acquireWorkItem(String workerId) throws IOException, InterruptedException {
        String url = String.format("%s/sessions/%s/backfill/work-items/acquire?worker_id=%s", 
                                  baseUrl, sessionName, workerId);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Content-Type", "application/json")
            .GET()
            .build();
        
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() == 404) {
            return null; // No available work items
        }
        
        if (response.statusCode() != 200) {
            throw new IOException("Failed to acquire work item. Status: " + response.statusCode() + ", Body: " + response.body());
        }
        
        return objectMapper.readTree(response.body());
    }
    
    /**
     * Renew a lease for a work item with optional progress update.
     */
    public JsonNode renewLease(String workItemId, String workerId, 
                              Integer documentsProcessed, Long bytesProcessed) throws IOException, InterruptedException {
        String url = String.format("%s/sessions/%s/backfill/work-items/%s/lease", 
                                  baseUrl, sessionName, workItemId);
        
        StringBuilder requestBodyBuilder = new StringBuilder();
        requestBodyBuilder.append(String.format("""
            {
                "worker_id": "%s"
            """, workerId));
        
        if (documentsProcessed != null && bytesProcessed != null) {
            requestBodyBuilder.append(String.format("""
                ,
                "progress": {
                    "documents_processed": %d,
                    "bytes_processed": %d
                }
                """, documentsProcessed, bytesProcessed));
        }
        
        requestBodyBuilder.append("}");
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Content-Type", "application/json")
            .PUT(HttpRequest.BodyPublishers.ofString(requestBodyBuilder.toString()))
            .build();
        
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            if (response.statusCode() == 409) {
                throw new LeaseNotOwnedByWorkerException("Work item is not owned by worker " + workerId);
            } else if (response.statusCode() == 410) {
                throw new LeaseExpiredException("Lease has expired for work item " + workItemId);
            }
            throw new IOException("Failed to renew lease. Status: " + response.statusCode() + ", Body: " + response.body());
        }
        
        return objectMapper.readTree(response.body());
    }
    
    /**
     * Mark a work item as completed.
     */
    public JsonNode completeWorkItem(String workItemId, String workerId) throws IOException, InterruptedException {
        String url = String.format("%s/sessions/%s/backfill/work-items/%s/complete", 
                                  baseUrl, sessionName, workItemId);
        
        String requestBody = String.format("\"%s\"", workerId);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Content-Type", "application/json")
            .PUT(HttpRequest.BodyPublishers.ofString(requestBody))
            .build();
        
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            if (response.statusCode() == 409) {
                throw new LeaseNotOwnedByWorkerException("Work item is not owned by worker " + workerId);
            } else if (response.statusCode() == 410) {
                throw new LeaseExpiredException("Lease has expired for work item " + workItemId);
            }
            throw new IOException("Failed to complete work item. Status: " + response.statusCode() + ", Body: " + response.body());
        }
        
        return objectMapper.readTree(response.body());
    }
    
    /**
     * Get work queue status for the session.
     */
    public JsonNode getWorkQueueStatus() throws IOException, InterruptedException {
        String url = String.format("%s/sessions/%s/backfill/work-items/status", baseUrl, sessionName);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Content-Type", "application/json")
            .GET()
            .build();
        
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            throw new IOException("Failed to get work queue status. Status: " + response.statusCode() + ", Body: " + response.body());
        }
        
        return objectMapper.readTree(response.body());
    }
    
    /**
     * Clean up expired leases.
     */
    public void cleanupExpiredLeases() throws IOException, InterruptedException {
        String url = String.format("%s/sessions/%s/backfill/work-items/cleanup-expired", baseUrl, sessionName);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(url))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.noBody())
            .build();
        
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            logger.warn("Failed to cleanup expired leases. Status: {}, Body: {}", response.statusCode(), response.body());
        }
    }
    
    // Exception classes
    public static class LeaseNotOwnedByWorkerException extends RuntimeException {
        public LeaseNotOwnedByWorkerException(String message) {
            super(message);
        }
    }
    
    public static class LeaseExpiredException extends RuntimeException {
        public LeaseExpiredException(String message) {
            super(message);
        }
    }
}
