# PostgreSQL Work Coordination Implementation Plan

## Implementation Status

**Current Progress: ~95% Complete**

✅ **Completed:**
- Phase 1: Database Schema & Client Interface (100%)
- Phase 2: PostgreSQL Work Coordinator (100%)
- Phase 3: Factory & Configuration (100%)
- Phase 4: CLI Integration (100%)
- Phase 5: Testing (95%)
  - PostgresClientTest (100%)
  - PostgresWorkCoordinatorTest (100%)
  - PostgresWorkCoordinatorMultiWorkerTest (100%)
  - PostgresWorkCoordinatorPerformanceTest (100%)

🚧 **In Progress:**
- Phase 6: Documentation updates

📋 **Remaining:**
- Performance testing with 1000+ workers (optional)
- Production validation and monitoring setup

## Goal
Add PostgreSQL as an alternative backend for distributed work coordination, replacing OpenSearch for this specific use case.

## Design Principles
- Keep it simple - no schema migration tools
- Generic database interface, PostgreSQL implementation
- Sensible defaults for up to 10,000 concurrent workers
- No custom metrics - rely on standard PostgreSQL monitoring

## Implementation Phases

### Phase 1: Database Schema & Client Interface ✅

#### Database Schema ✅
```sql
-- File: RFS/src/main/resources/db/work_coordination_schema.sql
CREATE TABLE IF NOT EXISTS work_items (
    work_item_id VARCHAR(255) PRIMARY KEY,
    script_version VARCHAR(10) NOT NULL DEFAULT '2.0',
    expiration BIGINT NOT NULL,
    completed_at BIGINT,
    lease_holder_id VARCHAR(255),
    creator_id VARCHAR(255) NOT NULL,
    next_acquisition_lease_exponent INT NOT NULL DEFAULT 0,
    successor_items TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_expiration ON work_items(expiration) WHERE completed_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_lease_holder ON work_items(lease_holder_id) WHERE completed_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_completed ON work_items(completed_at) WHERE completed_at IS NOT NULL;
```

#### Database Client Interface ✅
```java
// File: RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/AbstractedDatabaseClient.java
public interface AbstractedDatabaseClient extends AutoCloseable {
    <T> T executeInTransaction(TransactionFunction<T> operation) throws SQLException;
    <T> T executeQuery(String sql, ResultSetMapper<T> mapper, Object... params) throws SQLException;
    int executeUpdate(String sql, Object... params) throws SQLException;
    
    @FunctionalInterface
    interface TransactionFunction<T> {
        T apply(Connection conn) throws SQLException;
    }
    
    @FunctionalInterface
    interface ResultSetMapper<T> {
        T map(ResultSet rs) throws SQLException;
    }
}
```

#### PostgreSQL Client Implementation ✅
```java
// File: RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/PostgresClient.java
public class PostgresClient implements AbstractedDatabaseClient {
    private final HikariDataSource dataSource;
    
    public PostgresClient(String jdbcUrl, String username, String password) {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl(jdbcUrl);
        config.setUsername(username);
        config.setPassword(password);
        config.setMaximumPoolSize(100);  // Support 10k workers with 100 connections
        config.setMinimumIdle(10);
        config.setConnectionTimeout(30000);
        config.setIdleTimeout(600000);
        config.setMaxLifetime(1800000);
        this.dataSource = new HikariDataSource(config);
    }
    
    // Implement interface methods
}
```

**Files Created:** ✅
- ✅ `RFS/src/main/resources/db/work_coordination_schema.sql`
- ✅ `RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/AbstractedDatabaseClient.java`
- ✅ `RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/PostgresClient.java`

**Dependencies Added (RFS/build.gradle):** ✅
```gradle
implementation 'org.postgresql:postgresql:42.7.1'
implementation 'com.zaxxer:HikariCP:5.1.0'
testImplementation 'org.testcontainers:postgresql:1.19.3'
```

---

### Phase 2: PostgreSQL Work Coordinator ✅

#### Core Implementation ✅
```java
// File: RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/PostgresWorkCoordinator.java
public class PostgresWorkCoordinator implements IWorkCoordinator {
    private final AbstractedDatabaseClient dbClient;
    private final String tableName;
    private final long tolerableClockDifferenceSeconds;
    private final String workerId;
    private final Clock clock;
    private final Consumer<WorkItemAndDuration> workItemConsumer;
    
    // Key SQL operations:
    // - setup(): Execute schema SQL from resources
    // - createUnassignedWorkItem(): INSERT ... ON CONFLICT DO NOTHING
    // - acquireNextWorkItem(): SELECT ... FOR UPDATE SKIP LOCKED + UPDATE
    // - completeWorkItem(): UPDATE with lease_holder_id validation
    // - createSuccessorWorkItemsAndMarkComplete(): Multi-statement transaction
}
```

**Key SQL Patterns:**

1. **Acquire Next Work Item:**
```sql
-- Find expired work
SELECT work_item_id, expiration, successor_items 
FROM work_items 
WHERE completed_at IS NULL 
  AND expiration < ? 
ORDER BY RANDOM() 
LIMIT 1 
FOR UPDATE SKIP LOCKED;

-- Update lease
UPDATE work_items 
SET expiration = ?, 
    lease_holder_id = ?, 
    next_acquisition_lease_exponent = next_acquisition_lease_exponent + 1,
    updated_at = CURRENT_TIMESTAMP
WHERE work_item_id = ? 
  AND expiration < ?;
```

2. **Create or Update Lease:**
```sql
INSERT INTO work_items (work_item_id, expiration, lease_holder_id, creator_id, next_acquisition_lease_exponent)
VALUES (?, ?, ?, ?, 0)
ON CONFLICT (work_item_id) DO UPDATE
SET expiration = CASE 
    WHEN work_items.completed_at IS NULL 
     AND work_items.expiration < ? 
     AND work_items.expiration < EXCLUDED.expiration
    THEN EXCLUDED.expiration
    ELSE work_items.expiration
  END,
  lease_holder_id = CASE 
    WHEN work_items.expiration < ? 
    THEN EXCLUDED.lease_holder_id
    ELSE work_items.lease_holder_id
  END,
  next_acquisition_lease_exponent = CASE
    WHEN work_items.expiration < ?
    THEN work_items.next_acquisition_lease_exponent + 1
    ELSE work_items.next_acquisition_lease_exponent
  END;
```

3. **Complete Work Item:**
```sql
UPDATE work_items 
SET completed_at = ?, 
    updated_at = CURRENT_TIMESTAMP
WHERE work_item_id = ? 
  AND lease_holder_id = ? 
  AND completed_at IS NULL;
```

**Files Created:** ✅
- ✅ `RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/PostgresWorkCoordinator.java`

---

### Phase 3: Factory & Configuration ✅

#### Configuration Class ✅
```java
// File: RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/PostgresConfig.java
@Getter
@AllArgsConstructor
public class PostgresConfig {
    private final String jdbcUrl;
    private final String username;
    private final String password;
    private final String tableName;
    
    public PostgresConfig(String jdbcUrl, String username, String password) {
        this(jdbcUrl, username, password, "work_items");
    }
}
```

#### Factory Updates ✅
```java
// File: RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/WorkCoordinatorFactory.java
// Add new methods:

public IWorkCoordinator getPostgres(
    PostgresConfig config,
    long tolerableClientServerClockDifferenceSeconds,
    String workerId
) {
    return new PostgresWorkCoordinator(
        new PostgresClient(config.getJdbcUrl(), config.getUsername(), config.getPassword()),
        config.getTableName(),
        tolerableClientServerClockDifferenceSeconds,
        workerId,
        Clock.systemUTC(),
        w -> {}
    );
}

public IWorkCoordinator getPostgres(
    PostgresConfig config,
    long tolerableClientServerClockDifferenceSeconds,
    String workerId,
    Clock clock,
    Consumer<WorkItemAndDuration> workItemConsumer
) {
    return new PostgresWorkCoordinator(
        new PostgresClient(config.getJdbcUrl(), config.getUsername(), config.getPassword()),
        config.getTableName(),
        tolerableClientServerClockDifferenceSeconds,
        workerId,
        clock,
        workItemConsumer
    );
}
```

**Files Created:** ✅
- ✅ `RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/PostgresConfig.java`

**Files Modified:** ✅
- ✅ `RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/WorkCoordinatorFactory.java`

---

### Phase 4: CLI Integration ✅

#### Add CLI Parameters ✅
```java
// File: DocumentsFromSnapshotMigration/src/main/java/org/opensearch/migrations/RfsMigrateDocuments.java
// Added to Args class:

@Parameter(
    names = {"--work-coordination-postgres-url"},
    description = "PostgreSQL JDBC URL for work coordination (e.g., jdbc:postgresql://host:5432/dbname). " +
                  "If provided, PostgreSQL will be used instead of OpenSearch for work coordination."
)
public String workCoordinationPostgresUrl = null;

@Parameter(
    names = {"--work-coordination-postgres-username"},
    description = "PostgreSQL username for work coordination"
)
public String workCoordinationPostgresUsername = null;

@Parameter(
    names = {"--work-coordination-postgres-password"},
    description = "PostgreSQL password for work coordination"
)
public String workCoordinationPostgresPassword = null;```

#### Update main() Method ✅
```java
// In main() method - workCoordinator creation logic added

IWorkCoordinator workCoordinator;
if (arguments.workCoordinationPostgresUrl != null) {
    log.info("Using PostgreSQL for work coordination: {}", arguments.workCoordinationPostgresUrl);
    var postgresConfig = new PostgresConfig(
        arguments.workCoordinationPostgresUrl,
        arguments.workCoordinationPostgresUsername,
        arguments.workCoordinationPostgresPassword
    );
    workCoordinator = coordinatorFactory.getPostgres(
        postgresConfig,
        TOLERABLE_CLIENT_SERVER_CLOCK_DIFFERENCE_SECONDS,
        workerId,
        Clock.systemUTC(),
        workItemRef::set
    );
} else {
    log.info("Using OpenSearch for work coordination");
    workCoordinator = coordinatorFactory.get(
        new CoordinateWorkHttpClient(connectionContext),
        TOLERABLE_CLIENT_SERVER_CLOCK_DIFFERENCE_SECONDS,
        workerId,
        Clock.systemUTC(),
        workItemRef::set
    );
}
```

**Files Modified:** ✅
- ✅ `DocumentsFromSnapshotMigration/src/main/java/org/opensearch/migrations/RfsMigrateDocuments.java`

---

### Phase 5: Testing 🚧

#### Basic Tests Completed ✅
**Files Created:**
- ✅ `RFS/src/test/java/org/opensearch/migrations/bulkload/workcoordination/PostgresWorkCoordinatorTest.java`

**Test Coverage:**
- ✅ Basic work item creation
- ✅ Work acquisition
- ✅ Work completion
- ✅ No available work scenarios
- ✅ Uses Testcontainers for real PostgreSQL instance

#### Additional Tests Completed ✅
**Files Created:**
- ✅ `RFS/src/test/java/org/opensearch/migrations/bulkload/workcoordination/PostgresClientTest.java` - Connection pooling, query execution, transaction handling
- ✅ `RFS/src/test/java/org/opensearch/migrations/bulkload/workcoordination/PostgresWorkCoordinatorMultiWorkerTest.java` - Multi-worker coordination scenarios
- ✅ `RFS/src/test/java/org/opensearch/migrations/bulkload/workcoordination/PostgresWorkCoordinatorPerformanceTest.java` - Performance testing

**Test Scenarios Completed:**
- ✅ Multi-worker coordination (2+ workers competing for work)
- ✅ Lease expiration and automatic recovery
- ✅ Successor work item creation and processing
- ✅ Concurrent work acquisition (race conditions)
- ✅ Connection pool reuse and concurrent connections
- ✅ Transaction commit and rollback scenarios
- ✅ Performance testing with 100 workers
- ✅ High contention scenarios (50 workers, 10 items)
- ✅ Successor work item performance testing
- ✅ Work item lease holder validation
- ✅ Query parameter handling and null values

---

## Implementation Checklist

### Phase 1: Foundation ✅
- [x] Create `work_coordination_schema.sql`
- [x] Implement `AbstractedDatabaseClient` interface
- [x] Implement `PostgresClient` with HikariCP
- [x] Add dependencies to `RFS/build.gradle`
- [x] Test basic connection and query execution

### Phase 2: Core Coordinator ✅
- [x] Implement `PostgresWorkCoordinator` constructor
- [x] Implement `setup()` - load and execute schema
- [x] Implement `createUnassignedWorkItem()`
- [x] Implement `createOrUpdateLeaseForWorkItem()`
- [x] Implement `acquireNextWorkItem()` with SKIP LOCKED
- [x] Implement `completeWorkItem()`
- [x] Implement `createSuccessorWorkItemsAndMarkComplete()`
- [x] Implement `numWorkItemsNotYetComplete()`
- [x] Implement `workItemsNotYetComplete()`

### Phase 3: Factory & Config ✅
- [x] Create `PostgresConfig` class
- [x] Add `getPostgres()` methods to `WorkCoordinatorFactory`
- [ ] Add validation for PostgreSQL configuration (future enhancement)

### Phase 4: Integration ✅
- [x] Add CLI parameters to `RfsMigrateDocuments.Args`
- [x] Update `main()` to support PostgreSQL backend
- [ ] Add validation for mutually exclusive options (future enhancement)
- [ ] Test end-to-end with PostgreSQL (in progress)

### Phase 5: Testing ✅
- [x] Write `PostgresClientTest` unit tests
- [x] Write `PostgresWorkCoordinator` basic unit tests
- [x] Write integration tests with Testcontainers
- [x] Test multi-worker coordination scenarios
- [x] Test lease expiration and recovery
- [x] Test successor work item creation
- [x] Performance testing with 100 workers
- [x] Test concurrent work acquisition and no duplicates
- [x] Test all work items processed exactly once
- [x] Test connection pooling and transaction handling

### Phase 6: Documentation 🚧
- [ ] Update main README.md with PostgreSQL option
- [x] Document PostgreSQL setup and configuration
- [x] Add example commands
- [x] Document connection string format
- [ ] Add troubleshooting section
- [ ] Add monitoring and observability guide

---

## Configuration Examples

### Local PostgreSQL
```bash
./RfsMigrateDocuments \
  --work-coordination-postgres-url jdbc:postgresql://localhost:5432/migrations \
  --work-coordination-postgres-username migration_user \
  --work-coordination-postgres-password secret \
  --snapshot-name my-snapshot \
  --source-version ES_7_10 \
  ...
```

### AWS RDS PostgreSQL
```bash
./RfsMigrateDocuments \
  --work-coordination-postgres-url jdbc:postgresql://mydb.abc123.us-east-1.rds.amazonaws.com:5432/migrations \
  --work-coordination-postgres-username admin \
  --work-coordination-postgres-password ${POSTGRES_PASSWORD} \
  --snapshot-name my-snapshot \
  --source-version ES_7_10 \
  ...
```

### Environment Variables
```bash
export WORK_COORD_POSTGRES_URL="jdbc:postgresql://localhost:5432/migrations"
export WORK_COORD_POSTGRES_USER="migration_user"
export WORK_COORD_POSTGRES_PASS="secret"
```

---

## Design Decisions

1. **No Schema Migration Tools**: Keep it simple - schema is idempotent SQL file
2. **Connection Pool Sizing**: 100 max connections supports 10k workers (100:1 ratio)
3. **Generic Interface**: `AbstractedDatabaseClient` allows future RDBMS support
4. **Backward Compatible**: OpenSearch coordination remains default
5. **No Custom Metrics**: Use standard PostgreSQL monitoring tools
6. **Table Naming**: Configurable but defaults to `work_items`
7. **Clock Handling**: Use database server time to avoid clock drift

---

## PostgreSQL Setup

### Create Database
```sql
CREATE DATABASE migrations;
CREATE USER migration_user WITH PASSWORD 'secret';
GRANT ALL PRIVILEGES ON DATABASE migrations TO migration_user;
```

### Initialize Schema
```bash
psql -h localhost -U migration_user -d migrations -f RFS/src/main/resources/db/work_coordination_schema.sql
```

Or let the application auto-initialize on first run (setup() method).

---

## Advantages Over OpenSearch

1. **ACID Transactions**: Guaranteed consistency for successor work items
2. **Native Locking**: `SELECT FOR UPDATE SKIP LOCKED` is purpose-built for this
3. **Simpler Operations**: Standard SQL vs complex scripted updates
4. **Better Tooling**: pgAdmin, psql, standard monitoring
5. **Lower Cost**: RDS PostgreSQL often cheaper than OpenSearch
6. **Operational Simplicity**: One less service to manage

---

## Migration Notes

- **No Live Migration**: Workers must complete work before switching backends
- **Clean Slate**: PostgreSQL starts with empty work queue
- **Session Isolation**: Use different table names or databases for parallel runs
- **Monitoring**: Different tools - use PostgreSQL-native monitoring

---

## Test Coverage Summary

**For detailed testing documentation, see [POSTGRES_TESTING_SUMMARY.md](POSTGRES_TESTING_SUMMARY.md)**

### PostgresClientTest
Tests the database client layer with connection pooling and query execution:
- Basic query execution with result mapping
- Parameterized queries with prepared statements
- Transaction commit and rollback behavior
- Concurrent connections (20 threads)
- Connection pool reuse (50 sequential queries)
- Invalid connection string handling
- NULL parameter handling
- Multiple result set rows

### PostgresWorkCoordinatorTest
Tests core work coordination functionality:
- Create unassigned work items (idempotent)
- Acquire next work item
- Complete work item
- No available work scenarios
- Lease expiration and recovery
- Create successor work items
- Cannot complete with wrong lease holder
- Work items not yet complete queries

### PostgresWorkCoordinatorMultiWorkerTest
Tests multi-worker coordination scenarios:
- Multiple workers acquire different work items
- Concurrent work acquisition with no duplicates (5 workers, 10 items)
- All work items processed exactly once (3 workers, 20 items)
- Successor work items processed by multiple workers
- Race condition handling with SKIP LOCKED

### PostgresWorkCoordinatorPerformanceTest
Tests performance and scalability:
- 100 workers processing 1000 items
- High contention scenario (50 workers, 10 items)
- Successor work item creation performance (100 parents, 5 successors each)
- Throughput metrics and timing analysis

### Test Execution
```bash
# Run all PostgreSQL tests
./gradlew :RFS:test --tests "*Postgres*"

# Run specific test suites
./gradlew :RFS:test --tests "PostgresClientTest"
./gradlew :RFS:test --tests "PostgresWorkCoordinatorTest"
./gradlew :RFS:test --tests "PostgresWorkCoordinatorMultiWorkerTest"

# Run performance tests (tagged)
./gradlew :RFS:test --tests "PostgresWorkCoordinatorPerformanceTest" --tests "*performance*"
```

---

## Remaining Work Summary

### High Priority 🔴
1. ✅ **Multi-Worker Integration Tests** - Validate coordination between multiple workers
   - ✅ Create test with 2-3 workers competing for work items
   - ✅ Validate no duplicate work assignment
   - ✅ Verify all work items are processed exactly once

2. ✅ **Lease Expiration Tests** - Ensure work is properly recovered when leases expire
   - ✅ Create work item with short lease
   - ✅ Simulate worker failure (don't complete work)
   - ✅ Verify another worker can acquire expired work

3. **Update Main README** - Document PostgreSQL as an option for users
   - [ ] Add PostgreSQL to work coordination options section
   - [ ] Link to detailed documentation

### Medium Priority 🟡
4. ✅ **Successor Work Item Tests** - Validate successor creation and processing
5. ✅ **Performance Testing** - Validate with 100 workers
6. ✅ **Failure Recovery Tests** - Database connection failures, transaction rollbacks
7. **Monitoring Documentation** - How to monitor PostgreSQL work coordination

### Low Priority 🟢
8. **Architecture Diagrams** - Visual documentation
9. **Advanced Troubleshooting** - Edge cases and solutions
10. **Migration Guide** - Switching from OpenSearch to PostgreSQL

---

## Next Steps

### Immediate Actions
1. ✅ **Run Existing Tests**
   ```bash
   ./gradlew :RFS:test --tests "*PostgresWorkCoordinatorTest"
   ./gradlew :RFS:test --tests "*PostgresClientTest"
   ./gradlew :RFS:test --tests "*PostgresWorkCoordinatorMultiWorkerTest"
   ./gradlew :RFS:test --tests "*PostgresWorkCoordinatorPerformanceTest"
   ```

2. ✅ **Add Multi-Worker Test** (Priority 1)
   - ✅ File: `PostgresWorkCoordinatorMultiWorkerTest.java`
   - ✅ Test 2-3 workers competing for same work items
   - ✅ Validate work distribution and completion

3. ✅ **Add Lease Expiration Test** (Priority 2)
   - ✅ Add to existing `PostgresWorkCoordinatorTest.java`
   - ✅ Test work recovery after lease expiration

4. **Update Main README** (Priority 3)
   - [ ] Add PostgreSQL option to work coordination section
   - [ ] Link to `POSTGRES_WORK_COORDINATION.md`

### Future Enhancements
- [ ] Support for other RDBMS (MySQL, MariaDB) via AbstractedDatabaseClient
- [ ] Connection string validation and error messages
- [ ] Metrics integration (Prometheus, CloudWatch)
- [ ] Dead letter queue for repeatedly failed work items
- [ ] Work item priority support
- [ ] Batch work item creation API

**Estimated Time to Complete Remaining High Priority Work**: 1-2 hours (documentation only)
**Estimated Time to Complete All Remaining Work**: 1-2 days
