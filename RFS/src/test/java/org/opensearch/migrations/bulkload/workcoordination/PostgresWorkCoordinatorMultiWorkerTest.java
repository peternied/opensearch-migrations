package org.opensearch.migrations.bulkload.workcoordination;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.time.Clock;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

@Testcontainers
class PostgresWorkCoordinatorMultiWorkerTest {

    @Container
    private static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
        .withDatabaseName("test")
        .withUsername("test")
        .withPassword("test");

    private List<PostgresWorkCoordinator> coordinators;
    private AbstractedDatabaseClient dbClient;

    @BeforeEach
    void setUp() throws Exception {
        dbClient = new PostgresClient(
            postgres.getJdbcUrl(),
            postgres.getUsername(),
            postgres.getPassword()
        );
        
        coordinators = new ArrayList<>();
        var setupCoordinator = createCoordinator("setup-worker");
        setupCoordinator.setup(() -> null);
        setupCoordinator.close();
    }

    @AfterEach
    void tearDown() throws Exception {
        for (var coordinator : coordinators) {
            coordinator.close();
        }
        coordinators.clear();
    }

    private PostgresWorkCoordinator createCoordinator(String workerId) {
        var client = new PostgresClient(
            postgres.getJdbcUrl(),
            postgres.getUsername(),
            postgres.getPassword()
        );
        var coordinator = new PostgresWorkCoordinator(
            client,
            "work_items",
            30,
            workerId,
            Clock.systemUTC(),
            w -> {}
        );
        coordinators.add(coordinator);
        return coordinator;
    }

    @Test
    void testMultipleWorkersAcquireDifferentWorkItems() throws Exception {
        var coordinator1 = createCoordinator("worker-1");
        var coordinator2 = createCoordinator("worker-2");
        
        coordinator1.createUnassignedWorkItem("item-1", () -> null);
        coordinator1.createUnassignedWorkItem("item-2", () -> null);
        
        var acquired1 = new ArrayList<String>();
        var acquired2 = new ArrayList<String>();
        
        var outcome1 = coordinator1.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        outcome1.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
            @Override
            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                acquired1.add(workItem.getWorkItem().toString());
                return null;
            }
            @Override public Void onAlreadyCompleted() { return null; }
            @Override public Void onNoAvailableWorkToBeDone() { return null; }
        });
        
        var outcome2 = coordinator2.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        outcome2.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
            @Override
            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                acquired2.add(workItem.getWorkItem().toString());
                return null;
            }
            @Override public Void onAlreadyCompleted() { return null; }
            @Override public Void onNoAvailableWorkToBeDone() { return null; }
        });
        
        assertEquals(1, acquired1.size());
        assertEquals(1, acquired2.size());
        assertNotEquals(acquired1.get(0), acquired2.get(0), "Workers should acquire different items");
    }

    @Test
    void testConcurrentWorkAcquisitionNoDuplicates() throws Exception {
        var coordinator = createCoordinator("setup");
        for (int i = 0; i < 10; i++) {
            coordinator.createUnassignedWorkItem("item-" + i, () -> null);
        }
        
        int workerCount = 5;
        ExecutorService executor = Executors.newFixedThreadPool(workerCount);
        List<String> acquiredItems = Collections.synchronizedList(new ArrayList<>());
        CountDownLatch latch = new CountDownLatch(workerCount);
        
        for (int i = 0; i < workerCount; i++) {
            final String workerId = "worker-" + i;
            executor.submit(() -> {
                try {
                    var workerCoordinator = createCoordinator(workerId);
                    for (int j = 0; j < 3; j++) {
                        var outcome = workerCoordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
                        outcome.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
                            @Override
                            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                                acquiredItems.add(workItem.getWorkItem().toString());
                                return null;
                            }
                            @Override public Void onAlreadyCompleted() { return null; }
                            @Override public Void onNoAvailableWorkToBeDone() { return null; }
                        });
                    }
                } catch (Exception e) {
                    fail("Worker failed: " + e.getMessage());
                } finally {
                    latch.countDown();
                }
            });
        }
        
        assertTrue(latch.await(30, TimeUnit.SECONDS));
        executor.shutdown();
        
        assertEquals(10, acquiredItems.size(), "All items should be acquired");
        assertEquals(10, acquiredItems.stream().distinct().count(), "No duplicate acquisitions");
    }

    @Test
    void testAllWorkItemsProcessedExactlyOnce() throws Exception {
        var coordinator = createCoordinator("setup");
        int itemCount = 20;
        for (int i = 0; i < itemCount; i++) {
            coordinator.createUnassignedWorkItem("item-" + i, () -> null);
        }
        
        int workerCount = 3;
        ExecutorService executor = Executors.newFixedThreadPool(workerCount);
        AtomicInteger completedCount = new AtomicInteger(0);
        List<String> processedItems = Collections.synchronizedList(new ArrayList<>());
        
        for (int i = 0; i < workerCount; i++) {
            final String workerId = "worker-" + i;
            executor.submit(() -> {
                try {
                    var workerCoordinator = createCoordinator(workerId);
                    while (true) {
                        var outcome = workerCoordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
                        var acquired = new boolean[]{false};
                        var itemId = new String[1];
                        
                        outcome.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
                            @Override
                            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                                acquired[0] = true;
                                itemId[0] = workItem.getWorkItem().toString();
                                return null;
                            }
                            @Override public Void onAlreadyCompleted() { return null; }
                            @Override public Void onNoAvailableWorkToBeDone() { return null; }
                        });
                        
                        if (!acquired[0]) {
                            break;
                        }
                        
                        processedItems.add(itemId[0]);
                        workerCoordinator.completeWorkItem(itemId[0], () -> null);
                        completedCount.incrementAndGet();
                    }
                } catch (Exception e) {
                    fail("Worker failed: " + e.getMessage());
                }
            });
        }
        
        executor.shutdown();
        assertTrue(executor.awaitTermination(30, TimeUnit.SECONDS));
        
        assertEquals(itemCount, completedCount.get(), "All items should be completed");
        assertEquals(itemCount, processedItems.stream().distinct().count(), "No duplicate processing");
        assertEquals(0, coordinator.numWorkItemsNotYetComplete(() -> null), "No incomplete items");
    }

    @Test
    void testSuccessorWorkItemsProcessedByMultipleWorkers() throws Exception {
        var coordinator1 = createCoordinator("worker-1");
        var coordinator2 = createCoordinator("worker-2");
        
        coordinator1.createUnassignedWorkItem("parent-item", () -> null);
        
        var outcome = coordinator1.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        outcome.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
            @Override
            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                try {
                    coordinator1.createSuccessorWorkItemsAndMarkComplete(
                        "parent-item",
                        List.of("child-1", "child-2"),
                        () -> null
                    );
                } catch (Exception e) {
                    fail("Failed to create successors: " + e.getMessage());
                }
                return null;
            }
            @Override public Void onAlreadyCompleted() { return null; }
            @Override public Void onNoAvailableWorkToBeDone() { return null; }
        });
        
        var acquired = new ArrayList<String>();
        
        var outcome1 = coordinator1.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        outcome1.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
            @Override
            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                acquired.add(workItem.getWorkItem().toString());
                return null;
            }
            @Override public Void onAlreadyCompleted() { return null; }
            @Override public Void onNoAvailableWorkToBeDone() { return null; }
        });
        
        var outcome2 = coordinator2.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        outcome2.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
            @Override
            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                acquired.add(workItem.getWorkItem().toString());
                return null;
            }
            @Override public Void onAlreadyCompleted() { return null; }
            @Override public Void onNoAvailableWorkToBeDone() { return null; }
        });
        
        assertEquals(2, acquired.size(), "Both successor items should be acquired");
        assertTrue(acquired.contains("child-1"));
        assertTrue(acquired.contains("child-2"));
    }
}
