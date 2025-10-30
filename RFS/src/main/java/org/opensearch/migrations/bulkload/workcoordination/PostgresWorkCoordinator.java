package org.opensearch.migrations.bulkload.workcoordination;

import lombok.NonNull;
import lombok.extern.slf4j.Slf4j;
import org.opensearch.migrations.bulkload.tracing.IWorkCoordinationContexts;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Supplier;
import java.util.stream.Collectors;

@Slf4j
public class PostgresWorkCoordinator implements IWorkCoordinator {
    private final AbstractedDatabaseClient dbClient;
    private final String tableName;
    private final long tolerableClockDifferenceSeconds;
    private final String workerId;
    private final Clock clock;
    private final Consumer<WorkItemAndDuration> workItemConsumer;

    public PostgresWorkCoordinator(
        AbstractedDatabaseClient dbClient,
        String tableName,
        long tolerableClockDifferenceSeconds,
        String workerId,
        Clock clock,
        Consumer<WorkItemAndDuration> workItemConsumer
    ) {
        this.dbClient = dbClient;
        this.tableName = tableName;
        this.tolerableClockDifferenceSeconds = tolerableClockDifferenceSeconds;
        this.workerId = workerId;
        this.clock = clock;
        this.workItemConsumer = workItemConsumer;
    }

    @Override
    public Clock getClock() {
        return clock;
    }

    @Override
    public void setup(Supplier<IWorkCoordinationContexts.IInitializeCoordinatorStateContext> contextSupplier)
        throws IOException {
        try (var ctx = contextSupplier.get();
             var is = getClass().getResourceAsStream("/db/work_coordination_schema.sql");
             var reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8))) {
            
            String schema = reader.lines().collect(Collectors.joining("\n"));
            schema = schema.replace("work_items", tableName);
            
            dbClient.executeUpdate(schema);
            log.info("PostgreSQL work coordination schema initialized for table: {}", tableName);
        } catch (SQLException e) {
            throw new IOException("Failed to initialize schema", e);
        }
    }

    @Override
    public boolean createUnassignedWorkItem(
        String workItemId,
        Supplier<IWorkCoordinationContexts.ICreateUnassignedWorkItemContext> contextSupplier
    ) throws IOException {
        try (var ctx = contextSupplier.get()) {
            String sql = "INSERT INTO " + tableName + 
                " (work_item_id, expiration, creator_id) VALUES (?, 0, ?) ON CONFLICT (work_item_id) DO NOTHING";
            int rowsAffected = dbClient.executeUpdate(sql, workItemId, workerId);
            return rowsAffected > 0;
        } catch (SQLException e) {
            throw new IOException("Failed to create unassigned work item", e);
        }
    }

    @Override
    @NonNull
    public WorkAcquisitionOutcome createOrUpdateLeaseForWorkItem(
        String workItemId,
        Duration leaseDuration,
        Supplier<IWorkCoordinationContexts.IAcquireSpecificWorkContext> contextSupplier
    ) throws IOException, InterruptedException {
        try (var ctx = contextSupplier.get()) {
            long nowSeconds = clock.instant().getEpochSecond();
            long expirationSeconds = nowSeconds + leaseDuration.toSeconds();
            
            return dbClient.executeInTransaction(conn -> {
                String upsertSql = "INSERT INTO " + tableName + 
                    " (work_item_id, expiration, lease_holder_id, creator_id, next_acquisition_lease_exponent) " +
                    "VALUES (?, ?, ?, ?, 0) " +
                    "ON CONFLICT (work_item_id) DO UPDATE SET " +
                    "  expiration = CASE " +
                    "    WHEN " + tableName + ".completed_at IS NULL " +
                    "      AND " + tableName + ".expiration < ? " +
                    "      AND " + tableName + ".expiration < EXCLUDED.expiration " +
                    "    THEN EXCLUDED.expiration " +
                    "    ELSE " + tableName + ".expiration " +
                    "  END, " +
                    "  lease_holder_id = CASE " +
                    "    WHEN " + tableName + ".expiration < ? " +
                    "    THEN EXCLUDED.lease_holder_id " +
                    "    ELSE " + tableName + ".lease_holder_id " +
                    "  END, " +
                    "  next_acquisition_lease_exponent = CASE " +
                    "    WHEN " + tableName + ".expiration < ? " +
                    "    THEN " + tableName + ".next_acquisition_lease_exponent + 1 " +
                    "    ELSE " + tableName + ".next_acquisition_lease_exponent " +
                    "  END, " +
                    "  updated_at = CURRENT_TIMESTAMP " +
                    "RETURNING completed_at, expiration, lease_holder_id";
                
                try (PreparedStatement stmt = conn.prepareStatement(upsertSql)) {
                    stmt.setString(1, workItemId);
                    stmt.setLong(2, expirationSeconds);
                    stmt.setString(3, workerId);
                    stmt.setString(4, workerId);
                    stmt.setLong(5, nowSeconds);
                    stmt.setLong(6, nowSeconds);
                    stmt.setLong(7, nowSeconds);
                    
                    var rs = stmt.executeQuery();
                    if (rs.next()) {
                        Long completedAt = rs.getObject("completed_at", Long.class);
                        long expiration = rs.getLong("expiration");
                        String leaseHolder = rs.getString("lease_holder_id");
                        
                        if (completedAt != null) {
                            return new AlreadyCompleted();
                        } else if (leaseHolder != null && leaseHolder.equals(workerId) && expiration > nowSeconds) {
                            return new WorkItemAndDuration(
                                Instant.ofEpochSecond(expiration),
                                WorkItemAndDuration.WorkItem.valueFromWorkItemString(workItemId)
                            );
                        } else {
                            throw new LeaseLockHeldElsewhereException();
                        }
                    }
                    throw new SQLException("No result from upsert");
                }
            });
        } catch (SQLException e) {
            throw new IOException("Failed to create or update lease", e);
        }
    }

    @Override
    public WorkAcquisitionOutcome acquireNextWorkItem(
        Duration leaseDuration,
        Supplier<IWorkCoordinationContexts.IAcquireNextWorkItemContext> contextSupplier
    ) throws IOException, InterruptedException {
        try (var ctx = contextSupplier.get()) {
            long nowSeconds = clock.instant().getEpochSecond();
            
            return dbClient.executeInTransaction(conn -> {
                String selectSql = "SELECT work_item_id, next_acquisition_lease_exponent, successor_items " +
                    "FROM " + tableName + " " +
                    "WHERE completed_at IS NULL AND expiration < ? " +
                    "ORDER BY RANDOM() LIMIT 1 FOR UPDATE SKIP LOCKED";
                
                try (PreparedStatement selectStmt = conn.prepareStatement(selectSql)) {
                    selectStmt.setLong(1, nowSeconds);
                    var rs = selectStmt.executeQuery();
                    
                    if (!rs.next()) {
                        ctx.recordNothingAvailable();
                        return new NoAvailableWorkToBeDone();
                    }
                    
                    String workItemId = rs.getString("work_item_id");
                    int leaseExponent = rs.getInt("next_acquisition_lease_exponent");
                    String successorItems = rs.getString("successor_items");
                    
                    long adjustedLeaseDuration = (long) (Math.pow(2, leaseExponent) * leaseDuration.toSeconds());
                    long newExpiration = nowSeconds + adjustedLeaseDuration;
                    
                    String updateSql = "UPDATE " + tableName + " " +
                        "SET expiration = ?, lease_holder_id = ?, " +
                        "    next_acquisition_lease_exponent = next_acquisition_lease_exponent + 1, " +
                        "    updated_at = CURRENT_TIMESTAMP " +
                        "WHERE work_item_id = ?";
                    
                    try (PreparedStatement updateStmt = conn.prepareStatement(updateSql)) {
                        updateStmt.setLong(1, newExpiration);
                        updateStmt.setString(2, workerId);
                        updateStmt.setString(3, workItemId);
                        updateStmt.executeUpdate();
                    }
                    
                    if (successorItems != null && !successorItems.isEmpty()) {
                        List<String> successorList = List.of(successorItems.split(","));
                        try {
                            createSuccessorWorkItemsAndMarkComplete(workItemId, successorList, 0, 
                                ctx::getCreateSuccessorWorkItemsContext);
                            return acquireNextWorkItem(leaseDuration, contextSupplier);
                        } catch (IOException | InterruptedException e) {
                            throw new SQLException("Failed to handle successor items", e);
                        }
                    }
                    
                    ctx.recordAssigned();
                    var workItemAndDuration = new WorkItemAndDuration(
                        Instant.ofEpochSecond(newExpiration),
                        WorkItemAndDuration.WorkItem.valueFromWorkItemString(workItemId)
                    );
                    workItemConsumer.accept(workItemAndDuration);
                    return workItemAndDuration;
                }
            });
        } catch (SQLException e) {
            throw new IOException("Failed to acquire next work item", e);
        }
    }

    @Override
    public void completeWorkItem(
        String workItemId,
        Supplier<IWorkCoordinationContexts.ICompleteWorkItemContext> contextSupplier
    ) throws IOException {
        try (var ctx = contextSupplier.get()) {
            long nowSeconds = clock.instant().getEpochSecond();
            String sql = "UPDATE " + tableName + " " +
                "SET completed_at = ?, updated_at = CURRENT_TIMESTAMP " +
                "WHERE work_item_id = ? AND lease_holder_id = ? AND completed_at IS NULL";
            
            int rowsAffected = dbClient.executeUpdate(sql, nowSeconds, workItemId, workerId);
            if (rowsAffected == 0) {
                throw new IOException("Failed to complete work item - not owned by this worker or already completed");
            }
        } catch (SQLException e) {
            throw new IOException("Failed to complete work item", e);
        }
    }

    @Override
    public void createSuccessorWorkItemsAndMarkComplete(
        String workItemId,
        List<String> successorWorkItemIds,
        int initialNextAcquisitionLeaseExponent,
        Supplier<IWorkCoordinationContexts.ICreateSuccessorWorkItemsContext> contextSupplier
    ) throws IOException, InterruptedException {
        try (var ctx = contextSupplier.get()) {
            dbClient.executeInTransaction(conn -> {
                String updateSuccessorsSql = "UPDATE " + tableName + " " +
                    "SET successor_items = ?, updated_at = CURRENT_TIMESTAMP " +
                    "WHERE work_item_id = ? AND lease_holder_id = ?";
                
                try (PreparedStatement stmt = conn.prepareStatement(updateSuccessorsSql)) {
                    stmt.setString(1, String.join(",", successorWorkItemIds));
                    stmt.setString(2, workItemId);
                    stmt.setString(3, workerId);
                    stmt.executeUpdate();
                }
                
                String insertSuccessorSql = "INSERT INTO " + tableName + 
                    " (work_item_id, expiration, creator_id, next_acquisition_lease_exponent) " +
                    "VALUES (?, 0, ?, ?) ON CONFLICT (work_item_id) DO NOTHING";
                
                try (PreparedStatement stmt = conn.prepareStatement(insertSuccessorSql)) {
                    for (String successorId : successorWorkItemIds) {
                        stmt.setString(1, successorId);
                        stmt.setString(2, workerId);
                        stmt.setInt(3, initialNextAcquisitionLeaseExponent);
                        stmt.addBatch();
                    }
                    stmt.executeBatch();
                }
                
                long nowSeconds = clock.instant().getEpochSecond();
                String completeSql = "UPDATE " + tableName + " " +
                    "SET completed_at = ?, updated_at = CURRENT_TIMESTAMP " +
                    "WHERE work_item_id = ? AND lease_holder_id = ?";
                
                try (PreparedStatement stmt = conn.prepareStatement(completeSql)) {
                    stmt.setLong(1, nowSeconds);
                    stmt.setString(2, workItemId);
                    stmt.setString(3, workerId);
                    int rowsAffected = stmt.executeUpdate();
                    if (rowsAffected == 0) {
                        throw new SQLException("Failed to mark work item as complete");
                    }
                }
                
                return null;
            });
        } catch (SQLException e) {
            throw new IOException("Failed to create successor work items and mark complete", e);
        }
    }

    @Override
    public int numWorkItemsNotYetComplete(Supplier<IWorkCoordinationContexts.IPendingWorkItemsContext> contextSupplier)
        throws IOException {
        try (var ctx = contextSupplier.get()) {
            String sql = "SELECT COUNT(*) FROM " + tableName + " WHERE completed_at IS NULL";
            return dbClient.executeQuery(sql, rs -> {
                if (rs.next()) {
                    return rs.getInt(1);
                }
                return 0;
            });
        } catch (SQLException e) {
            throw new IOException("Failed to count incomplete work items", e);
        }
    }

    @Override
    public boolean workItemsNotYetComplete(Supplier<IWorkCoordinationContexts.IPendingWorkItemsContext> contextSupplier)
        throws IOException {
        return numWorkItemsNotYetComplete(contextSupplier) > 0;
    }

    @Override
    public void close() throws Exception {
        dbClient.close();
    }
}
