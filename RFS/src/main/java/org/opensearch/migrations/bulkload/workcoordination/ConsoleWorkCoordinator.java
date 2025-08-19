package org.opensearch.migrations.bulkload.workcoordination;

import com.fasterxml.jackson.databind.JsonNode;
import org.opensearch.migrations.bulkload.tracing.IWorkCoordinationContexts;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

/**
 * Implementation of IWorkCoordinator that uses the console_link API for work coordination.
 * This provides a simpler alternative to the OpenSearch-based coordination system.
 */
public class ConsoleWorkCoordinator implements IWorkCoordinator, AutoCloseable {
    private static final Logger logger = LoggerFactory.getLogger(ConsoleWorkCoordinator.class);
    
    private final ConsoleApiClient apiClient;
    private final String workerId;
    private final Map<String, ProgressTracker> progressTrackers = new HashMap<>();
    private final Clock clock;
    
    // Simple progress tracking helper
    private static class ProgressTracker {
        private final AtomicInteger documentsProcessed = new AtomicInteger(0);
        private final AtomicInteger bytesProcessed = new AtomicInteger(0);
        
        public void updateProgress(int docs, int bytes) {
            documentsProcessed.set(docs);
            bytesProcessed.set(bytes);
        }
        
        public int getDocumentsProcessed() {
            return documentsProcessed.get();
        }
        
        public int getBytesProcessed() {
            return bytesProcessed.get();
        }
    }
    
    public ConsoleWorkCoordinator(String baseUrl, String sessionName, String workerId) {
        this.apiClient = new ConsoleApiClient(baseUrl, sessionName);
        this.workerId = workerId;
        this.clock = Clock.systemUTC();
        logger.info("Initialized ConsoleWorkCoordinator for worker {} with session {}", workerId, sessionName);
    }
    
    @Override
    public void setup(Supplier<IWorkCoordinationContexts.IInitializeCoordinatorStateContext> contextSupplier) 
            throws IOException, InterruptedException {
        try (var context = contextSupplier.get()) {
            // Console-based coordination doesn't require setup like OpenSearch index creation
            // Just verify we can connect to the API
            try {
                apiClient.getWorkQueueStatus();
                logger.info("Successfully connected to console_link API");
            } catch (Exception e) {
                logger.error("Failed to connect to console_link API during setup", e);
                throw e;
            }
        }
    }
    
    @Override
    public boolean createUnassignedWorkItem(String workItemId, 
                                          Supplier<IWorkCoordinationContexts.ICreateUnassignedWorkItemContext> contextSupplier) 
            throws IOException {
        try (var context = contextSupplier.get()) {
            // For console coordination, we need additional metadata to create work items
            // This is a simplified implementation - in practice, you'd need to pass the metadata
            throw new UnsupportedOperationException(
                "createUnassignedWorkItem not supported in ConsoleWorkCoordinator. " +
                "Use createWorkItemWithMetadata instead or implement metadata extraction.");
        }
    }
    
    /**
     * Create a work item with full metadata (console-specific method).
     */
    public boolean createWorkItemWithMetadata(String workItemId, String indexName, int shardNumber, 
                                            int documentCount, long totalSizeBytes,
                                            Supplier<IWorkCoordinationContexts.ICreateUnassignedWorkItemContext> contextSupplier) 
            throws IOException, InterruptedException {
        try (var context = contextSupplier.get()) {
            try {
                apiClient.createWorkItem(workItemId, indexName, shardNumber, documentCount, totalSizeBytes);
                logger.info("Created work item {} for index {} shard {}", workItemId, indexName, shardNumber);
                return true;
            } catch (IOException e) {
                if (e.getMessage().contains("409")) {
                    // Work item already exists
                    logger.debug("Work item {} already exists", workItemId);
                    return false;
                }
                throw e;
            }
        }
    }
    
    @Override
    public WorkAcquisitionOutcome createOrUpdateLeaseForWorkItem(String workItemId, Duration leaseDuration,
                                                               Supplier<IWorkCoordinationContexts.IAcquireSpecificWorkContext> contextSupplier) 
            throws IOException, InterruptedException {
        try (var context = contextSupplier.get()) {
            // Console coordination doesn't support acquiring specific work items by ID
            // This would require extending the API or using acquireNextWorkItem instead
            throw new UnsupportedOperationException(
                "createOrUpdateLeaseForWorkItem not supported in ConsoleWorkCoordinator. " +
                "Use acquireNextWorkItem instead.");
        }
    }
    
    @Override
    public WorkAcquisitionOutcome acquireNextWorkItem(Duration leaseDuration,
                                                    Supplier<IWorkCoordinationContexts.IAcquireNextWorkItemContext> contextSupplier) 
            throws IOException, InterruptedException {
        try (var context = contextSupplier.get()) {
            try {
                JsonNode response = apiClient.acquireWorkItem(workerId);
                
                if (response == null) {
                    return new NoAvailableWorkToBeDone();
                }
                
                JsonNode workItem = response.get("work_item");
                String workItemId = workItem.get("work_item_id").asText();
                String leaseExpiryStr = workItem.get("lease_expiry").asText();
                Instant leaseExpiry = Instant.parse(leaseExpiryStr);
                
                // Initialize progress tracker for this work item
                progressTrackers.put(workItemId, new ProgressTracker());
                
                logger.info("Acquired work item {} with lease expiry {}", workItemId, leaseExpiry);
                
                return new WorkItemAndDuration(leaseExpiry, 
                    WorkItemAndDuration.WorkItem.valueFromWorkItemString(workItemId));
                
            } catch (ConsoleApiClient.LeaseExpiredException e) {
                throw new LeaseLockHeldElsewhereException();
            }
        }
    }
    
    @Override
    public void completeWorkItem(String workItemId,
                               Supplier<IWorkCoordinationContexts.ICompleteWorkItemContext> contextSupplier) 
            throws IOException, InterruptedException {
        try (var context = contextSupplier.get()) {
            try {
                apiClient.completeWorkItem(workItemId, workerId);
                
                // Clean up progress tracker
                progressTrackers.remove(workItemId);
                
                logger.info("Completed work item {}", workItemId);
                
            } catch (ConsoleApiClient.LeaseNotOwnedByWorkerException e) {
                throw new LeaseLockHeldElsewhereException();
            } catch (ConsoleApiClient.LeaseExpiredException e) {
                throw new LeaseLockHeldElsewhereException();
            }
        }
    }
    
    @Override
    public void createSuccessorWorkItemsAndMarkComplete(String workItemId, List<String> successorWorkItemIds,
                                                      int successorNextAcquisitionLeaseExponent,
                                                      Supplier<IWorkCoordinationContexts.ICreateSuccessorWorkItemsContext> contextSupplier) 
            throws IOException, InterruptedException {
        try (var context = contextSupplier.get()) {
            // Console coordination doesn't support successor work items in the same way
            // For now, just complete the current work item and let successors be created separately
            completeWorkItem(workItemId, context::getCompleteWorkItemContext);
            
            logger.warn("Successor work items not fully supported in ConsoleWorkCoordinator. " +
                       "Work item {} completed, but successors {} not created automatically.", 
                       workItemId, successorWorkItemIds);
        }
    }
    
    @Override
    public int numWorkItemsNotYetComplete(Supplier<IWorkCoordinationContexts.IPendingWorkItemsContext> contextSupplier) 
            throws IOException, InterruptedException {
        try (var context = contextSupplier.get()) {
            JsonNode status = apiClient.getWorkQueueStatus();
            int pending = status.get("pending_work_items").asInt();
            int assigned = status.get("assigned_work_items").asInt();
            return pending + assigned;
        }
    }
    
    @Override
    public boolean workItemsNotYetComplete(Supplier<IWorkCoordinationContexts.IPendingWorkItemsContext> contextSupplier) 
            throws IOException, InterruptedException {
        return numWorkItemsNotYetComplete(contextSupplier) > 0;
    }
    
    /**
     * Update progress for a work item and renew its lease.
     * This is a console-specific method that combines lease renewal with progress tracking.
     */
    public void updateProgressAndRenewLease(String workItemId, int documentsProcessed, long bytesProcessed) 
            throws IOException, InterruptedException {
        try {
            ProgressTracker tracker = progressTrackers.get(workItemId);
            if (tracker != null) {
                tracker.updateProgress(documentsProcessed, (int) bytesProcessed);
            }
            
            apiClient.renewLease(workItemId, workerId, documentsProcessed, bytesProcessed);
            
            logger.debug("Updated progress for work item {}: {}/{} documents, {} bytes", 
                        workItemId, documentsProcessed, "unknown", bytesProcessed);
            
        } catch (ConsoleApiClient.LeaseNotOwnedByWorkerException e) {
            throw new LeaseLockHeldElsewhereException();
        } catch (ConsoleApiClient.LeaseExpiredException e) {
            throw new LeaseLockHeldElsewhereException();
        }
    }
    
    /**
     * Get the current progress for a work item.
     */
    public int getDocumentsProcessed(String workItemId) {
        ProgressTracker tracker = progressTrackers.get(workItemId);
        return tracker != null ? tracker.getDocumentsProcessed() : 0;
    }
    
    /**
     * Get the current bytes processed for a work item.
     */
    public int getBytesProcessed(String workItemId) {
        ProgressTracker tracker = progressTrackers.get(workItemId);
        return tracker != null ? tracker.getBytesProcessed() : 0;
    }
    
    /**
     * Clean up expired leases across all work items.
     */
    public void cleanupExpiredLeases() {
        try {
            apiClient.cleanupExpiredLeases();
        } catch (Exception e) {
            logger.warn("Failed to cleanup expired leases", e);
        }
    }
    
    @Override
    public Clock getClock() {
        return clock;
    }
    
    @Override
    public void close() {
        // Clean up any resources
        progressTrackers.clear();
        logger.info("ConsoleWorkCoordinator closed for worker {}", workerId);
    }
}
