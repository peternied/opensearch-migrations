# Console Work Coordination Usage Guide

This document provides examples of how to use the new console_link-based work coordination system for RFS backfill operations.

## Configuration

### Console-based Coordination

```java
import org.opensearch.migrations.bulkload.workcoordination.*;

// Create configuration for console-based coordination
WorkCoordinationConfig config = UnifiedWorkCoordinatorFactory.createConsoleConfig(
    "http://localhost:8000",  // console_link API base URL
    "migration-session-1",    // session name
    "worker-001"              // worker ID
);

// Create factory
UnifiedWorkCoordinatorFactory factory = new UnifiedWorkCoordinatorFactory(version);

// Create work coordinator
IWorkCoordinator coordinator = factory.create(config);
```

### OpenSearch-based Coordination (Legacy)

```java
// Create configuration for OpenSearch-based coordination
WorkCoordinationConfig config = UnifiedWorkCoordinatorFactory.createOpenSearchConfig(
    httpClient,              // AbstractedHttpClient
    30,                      // tolerable clock difference in seconds
    "worker-001"             // worker ID
);

// Create work coordinator
IWorkCoordinator coordinator = factory.create(config);
```

## Basic Usage Flow

### 1. Setup and Initialization

```java
// Initialize the coordinator
coordinator.setup(() -> rootContext.createCoordinationInitializationStateContext());
```

### 2. Creating Work Items (Console-specific)

```java
// For console coordination, use the enhanced method with metadata
if (coordinator instanceof ConsoleWorkCoordinator) {
    ConsoleWorkCoordinator consoleCoordinator = (ConsoleWorkCoordinator) coordinator;
    
    boolean created = consoleCoordinator.createWorkItemWithMetadata(
        "index1_shard0",           // work item ID
        "my-index",                // index name
        0,                         // shard number
        50000,                     // document count
        1024000,                   // total size in bytes
        () -> rootContext.createUnassignedWorkContext()
    );
}
```

### 3. Acquiring Work Items

```java
// Acquire next available work item
WorkAcquisitionOutcome outcome = coordinator.acquireNextWorkItem(
    Duration.ofMinutes(5),     // lease duration
    () -> rootContext.createAcquireNextItemContext()
);

if (outcome instanceof WorkItemAndDuration) {
    WorkItemAndDuration workItem = (WorkItemAndDuration) outcome;
    String workItemId = workItem.getWorkItem().toString();
    Instant leaseExpiry = workItem.getLeaseExpirationTime();
    
    // Process the work item...
    processWorkItem(workItemId);
    
} else if (outcome instanceof NoAvailableWorkToBeDone) {
    // No work available
    Thread.sleep(5000);
}
```

### 4. Progress Updates (Console-specific)

```java
// Update progress and renew lease
if (coordinator instanceof ConsoleWorkCoordinator) {
    ConsoleWorkCoordinator consoleCoordinator = (ConsoleWorkCoordinator) coordinator;
    
    consoleCoordinator.updateProgressAndRenewLease(
        workItemId,
        documentsProcessed,   // int
        bytesProcessed        // long
    );
}
```

### 5. Completing Work Items

```java
// Mark work item as completed
coordinator.completeWorkItem(
    workItemId,
    () -> rootContext.createCompleteWorkContext()
);
```

## Console_link API Usage

### Creating Work Items via API

```bash
# Create a single work item
curl -X POST "http://localhost:8000/sessions/migration-session-1/backfill/work-items/" \
  -H "Content-Type: application/json" \
  -d '{
    "work_item_id": "index1_shard0",
    "index_name": "my-index",
    "shard_number": 0,
    "document_count": 50000,
    "total_size_bytes": 1024000
  }'

# Create multiple work items in batch
curl -X POST "http://localhost:8000/sessions/migration-session-1/backfill/work-items/batch" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "work_item_id": "index1_shard0",
      "index_name": "my-index",
      "shard_number": 0,
      "document_count": 50000,
      "total_size_bytes": 1024000
    },
    {
      "work_item_id": "index1_shard1",
      "index_name": "my-index",
      "shard_number": 1,
      "document_count": 45000,
      "total_size_bytes": 950000
    }
  ]'
```

### Acquiring Work Items

```bash
# Acquire next available work item
curl -X GET "http://localhost:8000/sessions/migration-session-1/backfill/work-items/acquire?worker_id=worker-001"
```

### Updating Progress

```bash
# Renew lease with progress update
curl -X PUT "http://localhost:8000/sessions/migration-session-1/backfill/work-items/index1_shard0/lease" \
  -H "Content-Type: application/json" \
  -d '{
    "worker_id": "worker-001",
    "progress": {
      "documents_processed": 25000,
      "bytes_processed": 512000
    }
  }'
```

### Monitoring Progress

```bash
# Get work queue status
curl -X GET "http://localhost:8000/sessions/migration-session-1/backfill/work-items/status"

# Response example:
{
  "session_name": "migration-session-1",
  "total_work_items": 10,
  "pending_work_items": 3,
  "assigned_work_items": 5,
  "completed_work_items": 2,
  "total_documents": 500000,
  "total_documents_processed": 150000,
  "total_size_bytes": 10240000,
  "total_bytes_processed": 3072000,
  "started_at": "2025-01-19T20:30:00Z",
  "last_update": "2025-01-19T20:35:00Z"
}
```

## Configuration Properties

For RFS applications, you can configure the coordination backend using these properties:

```properties
# Choose coordination backend
workcoordination.backend=console  # or 'opensearch'

# Console-specific configuration
workcoordination.console.baseUrl=http://localhost:8000
workcoordination.console.sessionName=migration-session-1

# Worker identification
workcoordination.workerId=worker-001
```

## Migration from OpenSearch Coordination

### Before (OpenSearch-based)

```java
WorkCoordinatorFactory factory = new WorkCoordinatorFactory(version, indexSuffix);
OpenSearchWorkCoordinator coordinator = factory.get(httpClient, clockDiff, workerId);
```

### After (Unified with Console support)

```java
UnifiedWorkCoordinatorFactory factory = new UnifiedWorkCoordinatorFactory(version, indexSuffix);
WorkCoordinationConfig config = UnifiedWorkCoordinatorFactory.createConsoleConfig(
    baseUrl, sessionName, workerId);
IWorkCoordinator coordinator = factory.create(config);
```

## Benefits of Console Coordination

1. **Simplified Lease Management**: 5-minute leases with simple renewal
2. **Real-time Progress Tracking**: UI can display live progress updates
3. **Better Observability**: All coordination data accessible via REST API
4. **Reduced Dependencies**: No OpenSearch cluster required for coordination
5. **Session Scoping**: Work items naturally grouped by migration session
6. **Metadata Rich**: Work items include index name, shard info, document counts
7. **Error Handling**: Clear HTTP status codes and error messages

## Troubleshooting

### Common Issues

1. **Work item not found (404)**: Check session name and work item ID
2. **Lease conflicts (409)**: Another worker owns the lease
3. **Lease expired (410)**: Lease expired, acquire new work item
4. **No available work (404 on acquire)**: No pending work items

### Debugging

```bash
# List all work items for a session
curl -X GET "http://localhost:8000/sessions/migration-session-1/backfill/work-items/"

# Get specific work item details
curl -X GET "http://localhost:8000/sessions/migration-session-1/backfill/work-items/index1_shard0"

# Clean up expired leases
curl -X POST "http://localhost:8000/sessions/migration-session-1/backfill/work-items/cleanup-expired"
