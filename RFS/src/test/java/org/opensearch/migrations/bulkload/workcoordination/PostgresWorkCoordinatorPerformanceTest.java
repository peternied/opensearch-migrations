package org.opensearch.migrations.bulkload.workcoordination;

import java.time.Clock;
import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.junit.jupiter.api.Assertions.*;

@Testcontainers
@Tag("performance")
class PostgresWorkCoordinatorPerformanceTest {

    @Container
    private static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
        .withDatabaseName("test")
        .withUsername("test")
        .withPassword("test");

    private List<PostgresWorkCoordinator> coordinators;

    @BeforeEach
    void setUp() throws Exception {
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
    void testPerformanceWith100Workers() throws Exception {
        int workerCount = 100;
        int itemsPerWorker = 10;
        int totalItems = workerCount * itemsPerWorker;
        
        var setupCoordinator = createCoordinator("setup");
        long startSetup = System.currentTimeMillis();
        for (int i = 0; i < totalItems; i++) {
            setupCoordinator.createUnassignedWorkItem("item-" + i, () -> null);
        }
        long setupTime = System.currentTimeMillis() - startSetup;
        System.out.println("Setup time for " + totalItems + " items: " + setupTime + "ms");
        
        ExecutorService executor = Executors.newFixedThreadPool(workerCount);
        AtomicInteger completedCount = new AtomicInteger(0);
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch doneLatch = new CountDownLatch(workerCount);
        
        long startTime = System.currentTimeMillis();
        
        for (int i = 0; i < workerCount; i++) {
            final String workerId = "worker-" + i;
            executor.submit(() -> {
                try {
                    startLatch.await();
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
                        
                        workerCoordinator.completeWorkItem(itemId[0], () -> null);
                        completedCount.incrementAndGet();
                    }
                } catch (Exception e) {
                    fail("Worker failed: " + e.getMessage());
                } finally {
                    doneLatch.countDown();
                }
            });
        }
        
        startLatch.countDown();
        assertTrue(doneLatch.await(120, TimeUnit.SECONDS), "Workers should complete within 2 minutes");
        
        long totalTime = System.currentTimeMillis() - startTime;
        executor.shutdown();
        
        assertEquals(totalItems, completedCount.get());
        assertEquals(0, setupCoordinator.numWorkItemsNotYetComplete(() -> null));
        
        System.out.println("Performance Results:");
        System.out.println("  Workers: " + workerCount);
        System.out.println("  Total Items: " + totalItems);
        System.out.println("  Total Time: " + totalTime + "ms");
        System.out.println("  Throughput: " + (totalItems * 1000.0 / totalTime) + " items/sec");
        System.out.println("  Avg Time per Item: " + (totalTime / (double)totalItems) + "ms");
    }

    @Test
    void testHighContentionScenario() throws Exception {
        int workerCount = 50;
        int itemCount = 10;
        
        var setupCoordinator = createCoordinator("setup");
        for (int i = 0; i < itemCount; i++) {
            setupCoordinator.createUnassignedWorkItem("item-" + i, () -> null);
        }
        
        ExecutorService executor = Executors.newFixedThreadPool(workerCount);
        List<String> acquiredItems = Collections.synchronizedList(new ArrayList<>());
        CountDownLatch startLatch = new CountDownLatch(1);
        CountDownLatch doneLatch = new CountDownLatch(workerCount);
        
        for (int i = 0; i < workerCount; i++) {
            final String workerId = "worker-" + i;
            executor.submit(() -> {
                try {
                    startLatch.await();
                    var workerCoordinator = createCoordinator(workerId);
                    
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
                } catch (Exception e) {
                    fail("Worker failed: " + e.getMessage());
                } finally {
                    doneLatch.countDown();
                }
            });
        }
        
        startLatch.countDown();
        assertTrue(doneLatch.await(30, TimeUnit.SECONDS));
        executor.shutdown();
        
        assertEquals(itemCount, acquiredItems.size());
        assertEquals(itemCount, acquiredItems.stream().distinct().count(), "No duplicate acquisitions under high contention");
    }

    @Test
    void testSuccessorWorkItemPerformance() throws Exception {
        int parentCount = 100;
        int successorsPerParent = 5;
        
        var coordinator = createCoordinator("worker");
        
        for (int i = 0; i < parentCount; i++) {
            coordinator.createUnassignedWorkItem("parent-" + i, () -> null);
        }
        
        long startTime = System.currentTimeMillis();
        
        for (int i = 0; i < parentCount; i++) {
            var outcome = coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
            final int parentIndex = i;
            
            outcome.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
                @Override
                public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                    try {
                        var successors = new ArrayList<String>();
                        for (int j = 0; j < successorsPerParent; j++) {
                            successors.add("child-" + parentIndex + "-" + j);
                        }
                        coordinator.createSuccessorWorkItemsAndMarkComplete(
                            workItem.getWorkItem().toString(),
                            successors,
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
        }
        
        long creationTime = System.currentTimeMillis() - startTime;
        
        int expectedSuccessors = parentCount * successorsPerParent;
        assertEquals(expectedSuccessors, coordinator.numWorkItemsNotYetComplete(() -> null));
        
        System.out.println("Successor Creation Performance:");
        System.out.println("  Parents: " + parentCount);
        System.out.println("  Successors per Parent: " + successorsPerParent);
        System.out.println("  Total Successors: " + expectedSuccessors);
        System.out.println("  Creation Time: " + creationTime + "ms");
        System.out.println("  Avg Time per Parent: " + (creationTime / (double)parentCount) + "ms");
    }
}
