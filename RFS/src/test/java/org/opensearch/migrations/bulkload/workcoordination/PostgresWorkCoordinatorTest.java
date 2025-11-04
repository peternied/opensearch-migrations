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
    private DatabaseClient dbClient;

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
            "test-worker-1",
            Clock.systemUTC(),
            w -> {}
        );
        
        coordinator.setup(() -> null);
    }

    @AfterEach
    void tearDown() throws Exception {
        if (dbClient != null && dbClient instanceof PostgresClient) {
            try {
                ((PostgresClient) dbClient).executeUpdate("DROP TABLE IF EXISTS work_items CASCADE");
            } catch (Exception e) {
                // Ignore cleanup errors
            }
        }
        if (coordinator != null) {
            coordinator.close();
        }
    }

    @Test
    void testCreateUnassignedWorkItem() throws Exception {
        boolean created = coordinator.createUnassignedWorkItem("index__0__0", () -> null);
        assertTrue(created, "First creation should return true");
        
        boolean createdAgain = coordinator.createUnassignedWorkItem("index__0__0", () -> null);
        assertFalse(createdAgain, "Second creation should return false");
    }

    @Test
    void testAcquireNextWorkItem() throws Exception {
        coordinator.createUnassignedWorkItem("index__0__0", () -> null);
        
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
                assertEquals("index__0__0", workItem.getWorkItem().toString());
                return null;
            }
        });
    }

    @Test
    void testCompleteWorkItem() throws Exception {
        coordinator.createUnassignedWorkItem("index__0__0", () -> null);
        coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        
        assertDoesNotThrow(() -> coordinator.completeWorkItem("index__0__0", () -> null));
        
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
        coordinator.createUnassignedWorkItem("index__0__0", () -> null);
        
        var shortLeaseCoordinator = new PostgresWorkCoordinator(
            dbClient,
            "work_items",
            "worker-with-short-lease",
            Clock.systemUTC(),
            w -> {}
        );
        
        shortLeaseCoordinator.acquireNextWorkItem(Duration.ofSeconds(1), () -> null);
        
        Thread.sleep(1500);
        
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
                assertEquals("index__0__0", workItem.getWorkItem().toString());
                return null;
            }
        });
        
        shortLeaseCoordinator.close();
    }

    @Test
    void testCreateSuccessorWorkItems() throws Exception {
        coordinator.createUnassignedWorkItem("index__0__0", () -> null);
        coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        
        coordinator.createSuccessorWorkItemsAndMarkComplete(
            "index__0__0",
            java.util.List.of("index__1__0", "index__2__0"),
            0,
            () -> null
        );
        
        int remaining = coordinator.numWorkItemsNotYetComplete(() -> null);
        assertEquals(2, remaining, "Should have 2 successor items");
        
        // Verify successor items exist by checking count
        assertTrue(coordinator.workItemsNotYetComplete(() -> null));
    }

    @Test
    void testCannotCompleteWorkItemWithWrongLeaseHolder() throws Exception {
        coordinator.createUnassignedWorkItem("index__0__0", () -> null);
        coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        
        var otherCoordinator = new PostgresWorkCoordinator(
            dbClient,
            "work_items",
            "other-worker",
            Clock.systemUTC(),
            w -> {}
        );
        
        assertThrows(Exception.class, () -> {
            otherCoordinator.completeWorkItem("index__0__0", () -> null);
        });
        
        otherCoordinator.close();
    }

    @Test
    void testWorkItemsNotYetComplete() throws Exception {
        coordinator.createUnassignedWorkItem("index__0__0", () -> null);
        coordinator.createUnassignedWorkItem("index__1__0", () -> null);
        coordinator.createUnassignedWorkItem("index__2__0", () -> null);
        
        assertEquals(3, coordinator.numWorkItemsNotYetComplete(() -> null));
        
        coordinator.acquireNextWorkItem(Duration.ofMinutes(5), () -> null);
        coordinator.completeWorkItem("index__0__0", () -> null);
        
        assertEquals(2, coordinator.numWorkItemsNotYetComplete(() -> null));
        
        assertTrue(coordinator.workItemsNotYetComplete(() -> null));
    }
}
