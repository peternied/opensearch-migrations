# Backfill Work Coordination System Design

## Overview

This document describes the design and implementation of a new work coordination system for RFS backfill operations, built on the console_link API infrastructure. This system replaces the existing OpenSearch-based work coordination with a RESTful API approach that provides better observability, progress tracking, and integration with the migration console.

## Architecture

### Components

1. **Console_link API Extensions** - New FastAPI endpoints for work coordination
2. **TinyDB Storage Layer** - Lightweight database for work item persistence
3. **Java HTTP Client** - RFS integration layer
4. **ConsoleWorkCoordinator** - New IWorkCoordinator implementation
5. **Progress Tracking** - Real-time progress updates during lease renewals

### High-Level Flow

```
RFS Workers → ConsoleWorkCoordinator → HTTP Client → Console_link API → TinyDB
                                                            ↓
                                              Migration Console UI
```

## API Design

### Base Path
All backfill work coordination endpoints are under:
`/sessions/{session_name}/backfill/work-items`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/sessions/{session_name}/backfill/work-items` | Create work items |
| GET | `/sessions/{session_name}/backfill/work-items/acquire` | Acquire next available work item |
| PUT | `/sessions/{session_name}/backfill/work-items/{work_item_id}/lease` | Renew lease with progress update |
| PUT | `/sessions/{session_name}/backfill/work-items/{work_item_id}/complete` | Mark work item complete |
| POST | `/sessions/{session_name}/backfill/work-items/{work_item_id}/successors` | Create successor work items |
| GET | `/sessions/{session_name}/backfill/work-items/status` | Get queue status and progress |

### Request/Response Models

#### BackfillWorkItem
```python
class BackfillWorkItem(BaseModel):
    work_item_id: str
    session_name: str
    status: WorkItemStatus  # PENDING, ASSIGNED, COMPLETED
    
    # Shard metadata
    index_name: str
    shard_number: int
    document_count: int
    total_size_bytes: int
    
    # Lease management
    worker_id: Optional[str] = None
    lease_expiry: Optional[datetime] = None
    
    # Progress tracking
    documents_processed: int = 0
    bytes_processed: int = 0
    last_progress_update: Optional[datetime] = None
    
    # Timing
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
```

#### Progress Update
```python
class ProgressUpdate(BaseModel):
    documents_processed: int
    bytes_processed: int
```

#### Lease Renewal Request
```python
class LeaseRenewalRequest(BaseModel):
    worker_id: str
    progress: Optional[ProgressUpdate] = None
```

#### Work Item Creation Request
```python
class CreateWorkItemRequest(BaseModel):
    work_item_id: str
    index_name: str
    shard_number: int
    document_count: int
    total_size_bytes: int
```

## Data Model

### Work Item Status Lifecycle
```
PENDING → ASSIGNED → COMPLETED
    ↑         ↓
    └─────────┘ (lease expiry)
```

### Database Schema (TinyDB)

#### work_items table
- work_item_id (primary key)
- session_name
- status
- index_name
- shard_number
- document_count
- total_size_bytes
- worker_id
- lease_expiry
- documents_processed
- bytes_processed
- last_progress_update
- created_at
- started_at
- completed_at

## Configuration

### RFS Configuration
New configuration option to choose work coordination backend:
```properties
workcoordination.backend=console  # or 'opensearch'
workcoordination.console.baseUrl=http://localhost:8000
workcoordination.console.sessionName=migration-session-1
```

### Console_link Configuration
TinyDB file location and lease timeout settings.

## Lease Management

### Simplified Approach
- **Default Lease Duration**: 5 minutes
- **Renewal**: Workers must renew leases before expiry
- **Expiry Handling**: Expired leases automatically make work items available
- **No Complex Backoff**: Simple timeout-based approach

### Lease Renewal with Progress
When workers renew leases, they can optionally provide progress updates:
- Documents processed so far
- Bytes processed so far
- Timestamp of last update

This enables real-time progress monitoring in the UI.

## Error Handling

### API Errors
- 404: Session or work item not found
- 409: Work item already assigned to another worker
- 410: Lease expired
- 422: Invalid request data

### Retry Strategy
- Simple exponential backoff for transient failures
- No retries for client errors (4xx)
- Maximum retry attempts configurable

## Integration with Existing RFS

### IWorkCoordinator Implementation
The new `ConsoleWorkCoordinator` implements the existing `IWorkCoordinator` interface, ensuring seamless integration with existing RFS workflows.

### Factory Pattern
```java
public class WorkCoordinatorFactory {
    public static IWorkCoordinator create(WorkCoordinationConfig config) {
        switch (config.getBackend()) {
            case CONSOLE:
                return new ConsoleWorkCoordinator(config);
            case OPENSEARCH:
                return new OpenSearchWorkCoordinator(config);
            default:
                throw new IllegalArgumentException("Unknown backend: " + config.getBackend());
        }
    }
}
```

## Progress Tracking and UI Integration

### Real-time Progress
- Work items track documents and bytes processed
- Progress updates sent during lease renewals
- UI can display:
  - Per-work-item progress bars
  - Overall migration progress
  - Throughput metrics
  - ETA calculations

### Grouping and Filtering
- Work items can be grouped by index name
- Progress shown per shard and per index
- Filtering by status, worker, or time ranges

## Deployment Considerations

### Fresh Deployment
- System assumes fresh deployment (no migration from existing OpenSearch work items)
- Workers start with empty work queue
- Work items created as needed by migration process

### Scaling
- TinyDB suitable for single-instance deployments
- Future upgrade path to PostgreSQL/MySQL for multi-instance scenarios
- Horizontal scaling through session partitioning

## Testing Strategy

### Unit Tests
- Model validation
- Database operations
- API endpoint testing
- Java client testing

### Integration Tests
- End-to-end work coordination flow
- Lease expiry handling
- Progress tracking accuracy
- Error scenarios

## Migration Path

### Phase 1: Parallel Implementation
- Implement console_link backend alongside existing OpenSearch backend
- Configuration-driven selection
- Feature parity testing

### Phase 2: Transition
- Default to console_link backend for new deployments
- Performance and reliability validation
- Documentation updates

### Phase 3: Deprecation
- Mark OpenSearch backend as deprecated
- Migration guide for existing deployments
- Eventual removal of OpenSearch dependency

## Future Enhancements

### Potential Improvements
1. **Database Upgrade**: Move from TinyDB to PostgreSQL for better performance
2. **Advanced Scheduling**: Priority-based work item scheduling
3. **Worker Health Monitoring**: Track worker performance and health
4. **Batch Operations**: Bulk work item creation and status updates
5. **Metrics Integration**: Detailed metrics and alerting
6. **Work Item Dependencies**: Support for dependent work items

### API Versioning
Future API changes will be versioned (e.g., `/v2/sessions/{session_name}/backfill/work-items`)

## Security Considerations

### Authentication
- Leverage existing console_link session authentication
- Worker authentication through API keys or session tokens

### Authorization
- Session-scoped access control
- Workers can only access work items for their assigned session

### Data Validation
- Input validation on all API endpoints
- Sanitization of work item IDs and metadata

---

This design provides a solid foundation for replacing the OpenSearch-based work coordination system with a more maintainable, observable, and user-friendly alternative.
