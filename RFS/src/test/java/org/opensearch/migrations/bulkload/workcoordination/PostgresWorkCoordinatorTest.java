package org.opensearch.migrations.bulkload.workcoordination;

import java.time.Clock;
import java.time.Duration;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.junit.jupiter.api.Assertions.*;

@Testcontainers
class PostgresWorkCoordinatorTest {

    @Container
    private static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
        .withDatabaseName("test")
        .withUsername("test")
        .withPassword("test");

    private PostgresWorkCoordinator coordinator;
    private AbstractedDatabaseClient dbClient;

    @BeforeEach
    void setUp() throws Exception {
        dbClient = new PostgresClient(
            postgres.getJdbcUrl(),
            postgres.getUsername(),
            postgres.getPassword()
        );
        
        coordinator = new PostgresWorkCoordinator(
            dbClient,
            "work_items",
            30,
            "test-worker-1",
            Clock.systemUTC(),
            w -> {}
        );
        
        coordinator.setup(() -> null);
    }

    @AfterEach
    void tearDown() throws Exception {
        if (coordinator != null) {
            coordinator.close();
        }
    }

    @Test
    void testCreateUnassignedWorkItem() throws Exception {
        boolean created = coordinator.createUnassignedWorkItem("test-item-1", () -> null);
        assertTrue(created, "First creation should return true");
        
        boolean createdAgain = coordinator.createUnassignedWorkItem("test-item-1", () -> null);
        assertFalse(createdAgain, "Second creation should return false");
    }

    @Test
    void testAcquireNextWorkItem() throws Exception {
        coordinator.createUnassignedWorkItem("test-item-1", () -> null);
        
        var outcome = coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        
        assertNotNull(outcome);
        outcome.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
            @Override
            public Void onAlreadyCompleted() {
                fail("Should not be already completed");
                return null;
            }

            @Override
            public Void onNoAvailableWorkToBeDone() {
                fail("Should have work available");
                return null;
            }

            @Override
            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                assertEquals("test-item-1", workItem.getWorkItem().toString());
                return null;
            }
        });
    }

    @Test
    void testCompleteWorkItem() throws Exception {
        coordinator.createUnassignedWorkItem("test-item-1", () -> null);
        coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        
        assertDoesNotThrow(() -> coordinator.completeWorkItem("test-item-1", () -> null));
        
        int remaining = coordinator.numWorkItemsNotYetComplete(() -> null);
        assertEquals(0, remaining);
    }

    @Test
    void testNoAvailableWork() throws Exception {
        var outcome = coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        
        outcome.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
            @Override
            public Void onAlreadyCompleted() {
                fail("Should not be already completed");
                return null;
            }

            @Override
            public Void onNoAvailableWorkToBeDone() {
                return null;
            }

            @Override
            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                fail("Should have no work available");
                return null;
            }
        });
    }

    @Test
    void testLeaseExpirationAndRecovery() throws Exception {
        coordinator.createUnassignedWorkItem("test-item-1", () -> null);
        
        var shortLeaseCoordinator = new PostgresWorkCoordinator(
            dbClient,
            "work_items",
            30,
            "worker-with-short-lease",
            Clock.systemUTC(),
            w -> {}
        );
        
        shortLeaseCoordinator.acquireNextWorkItem(Duration.ofMillis(100), () -> null);
        
        Thread.sleep(200);
        
        var outcome = coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        
        outcome.visit(new IWorkCoordinator.WorkAcquisitionOutcomeVisitor<Void>() {
            @Override
            public Void onAlreadyCompleted() {
                fail("Should not be already completed");
                return null;
            }

            @Override
            public Void onNoAvailableWorkToBeDone() {
                fail("Expired work should be available");
                return null;
            }

            @Override
            public Void onAcquiredWork(IWorkCoordinator.WorkItemAndDuration workItem) {
                assertEquals("test-item-1", workItem.getWorkItem().toString());
                return null;
            }
        });
        
        shortLeaseCoordinator.close();
    }

    @Test
    void testCreateSuccessorWorkItems() throws Exception {
        coordinator.createUnassignedWorkItem("parent-item", () -> null);
        coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        
        coordinator.createSuccessorWorkItemsAndMarkComplete(
            "parent-item",
            java.util.List.of("child-1", "child-2"),
            () -> null
        );
        
        int remaining = coordinator.numWorkItemsNotYetComplete(() -> null);
        assertEquals(2, remaining, "Should have 2 successor items");
        
        var items = coordinator.workItemsNotYetComplete(() -> null);
        assertTrue(items.contains("child-1"));
        assertTrue(items.contains("child-2"));
    }

    @Test
    void testCannotCompleteWorkItemWithWrongLeaseHolder() throws Exception {
        coordinator.createUnassignedWorkItem("test-item-1", () -> null);
        coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        
        var otherCoordinator = new PostgresWorkCoordinator(
            dbClient,
            "work_items",
            30,
            "other-worker",
            Clock.systemUTC(),
            w -> {}
        );
        
        assertThrows(Exception.class, () -> {
            otherCoordinator.completeWorkItem("test-item-1", () -> null);
        });
        
        otherCoordinator.close();
    }

    @Test
    void testWorkItemsNotYetComplete() throws Exception {
        coordinator.createUnassignedWorkItem("item-1", () -> null);
        coordinator.createUnassignedWorkItem("item-2", () -> null);
        coordinator.createUnassignedWorkItem("item-3", () -> null);
        
        assertEquals(3, coordinator.numWorkItemsNotYetComplete(() -> null));
        
        coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        coordinator.completeWorkItem("item-1", () -> null);
        
        assertEquals(2, coordinator.numWorkItemsNotYetComplete(() -> null));
        
        var remaining = coordinator.workItemsNotYetComplete(() -> null);
        assertEquals(2, remaining.size());
        assertFalse(remaining.contains("item-1"));
    }
}
