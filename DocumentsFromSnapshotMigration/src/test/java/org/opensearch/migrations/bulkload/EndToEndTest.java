package org.opensearch.migrations.bulkload;

import java.io.File;
import java.util.List;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

import org.opensearch.migrations.Version;
import org.opensearch.migrations.bulkload.common.FileSystemRepo;
import org.opensearch.migrations.bulkload.common.FileSystemSnapshotCreator;
import org.opensearch.migrations.bulkload.common.OpenSearchClientFactory;
import org.opensearch.migrations.bulkload.common.RestClient;
import org.opensearch.migrations.bulkload.common.http.ConnectionContextTestParams;
import org.opensearch.migrations.bulkload.framework.SearchClusterContainer;
import org.opensearch.migrations.bulkload.http.ClusterOperations;
import org.opensearch.migrations.bulkload.worker.SnapshotRunner;
import org.opensearch.migrations.bulkload.workcoordination.PostgresConfig;
import org.opensearch.migrations.cluster.ClusterProviderRegistry;
import org.opensearch.migrations.reindexer.tracing.DocumentMigrationTestContext;
import org.opensearch.migrations.snapshot.creation.tracing.SnapshotTestContext;

import lombok.SneakyThrows;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.Mockito;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.lifecycle.Startables;

@Tag("isolatedTest")
@Testcontainers
public class EndToEndTest extends SourceTestBase {
    @TempDir
    private File localDirectory;
    
    @Container
    private static final PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15-alpine")
        .withDatabaseName("test")
        .withUsername("test")
        .withPassword("test");
    
    private PostgresConfig postgresConfig;
    
    private static final String SERVERLESS_ENDPOINT = "https://aurfb38nmcwqqqf7zmxj.eu-west-1.aoss.amazonaws.com";
    
    @BeforeEach
    void setUp() {
        postgresConfig = new PostgresConfig(
            postgres.getJdbcUrl(),
            postgres.getUsername(),
            postgres.getPassword()
        );
    }

    @Test
    public void migrationToServerless() {
        try (final var sourceCluster = new SearchClusterContainer(SearchClusterContainer.OS_V2_19_1)) {
            migrationDocumentsWithClusters(sourceCluster);
        }
    }

    @SneakyThrows
    private void migrationDocumentsWithClusters(final SearchClusterContainer sourceCluster) {
        final var snapshotContext = SnapshotTestContext.factory().noOtelTracking();
        final var testDocMigrationContext = DocumentMigrationTestContext.factory().noOtelTracking();

        try {
            // === ACTION: Set up source cluster ===
            Startables.deepStart(sourceCluster).join();

            var indexName = "blog_2023";
            var numberOfShards = 1;
            var sourceClusterOperations = new ClusterOperations(sourceCluster);
            
            // Create mock target cluster for migration
            var mockTargetCluster = Mockito.mock(SearchClusterContainer.class);
            Mockito.when(mockTargetCluster.getUrl()).thenReturn(SERVERLESS_ENDPOINT);
            Mockito.when(mockTargetCluster.getContainerVersion()).thenReturn(SearchClusterContainer.OS_V2_19_1);

            // Create simple index for source cluster
            String indexBody = String.format(
                "{" +
                "  \"settings\": {" +
                "    \"number_of_shards\": %d," +
                "    \"number_of_replicas\": 0," +
                "    \"refresh_interval\": -1" +
                "  }" +
                "}",
                numberOfShards
            );
            sourceClusterOperations.createIndex(indexName, indexBody);

            // === ACTION: Create simple test documents ===
            sourceClusterOperations.createDocument(indexName, "1", "{\"score\": 42}");
            sourceClusterOperations.createDocument(indexName, "2", "{\"score\": 55, \"active\": true}");
            sourceClusterOperations.createDocument(indexName, "3", "{\"score\": 60, \"active\": true}");
            sourceClusterOperations.post("/" + indexName + "/_refresh", null);

            // === ACTION: Take a snapshot ===
            var snapshotName = "my_snap";
            var snapshotRepoName = "my_snap_repo";
            var sourceClientFactory = new OpenSearchClientFactory(ConnectionContextTestParams.builder()
                    .host(sourceCluster.getUrl())
                    .insecure(true)
                    .build()
                    .toConnectionContext());
            var sourceClient = sourceClientFactory.determineVersionAndCreate();
            var snapshotCreator = new FileSystemSnapshotCreator(
                snapshotName,
                snapshotRepoName,
                sourceClient,
                SearchClusterContainer.CLUSTER_SNAPSHOT_DIR,
                List.of(),
                snapshotContext.createSnapshotCreateContext()
            );
            SnapshotRunner.runAndWaitForCompletion(snapshotCreator);
            sourceCluster.copySnapshotData(localDirectory.toString());
            var fileFinder = ClusterProviderRegistry.getSnapshotFileFinder(
                    sourceCluster.getContainerVersion().getVersion(), true);
            var sourceRepo = new FileSystemRepo(localDirectory.toPath(), fileFinder);

            // === ACTION: Migrate the documents ===
            var runCounter = new AtomicInteger();
            var clockJitter = new Random(1);

            // ExpectedMigrationWorkTerminationException is thrown on completion.
            var expectedTerminationException = waitForRfsCompletion(() -> migrateDocumentsSequentiallyWithPostgres(
                    sourceRepo,
                    snapshotName,
                    List.of(),
                    mockTargetCluster,
                    runCounter,
                    clockJitter,
                    testDocMigrationContext,
                    sourceCluster.getContainerVersion().getVersion(),
                    mockTargetCluster.getContainerVersion().getVersion(),
                    null,
                    postgresConfig
            ));

            Assertions.assertTrue(expectedTerminationException.numRuns > 0);
            System.out.println("Migration to serverless completed successfully with " + expectedTerminationException.numRuns + " runs");
        } finally {
            deleteTree(localDirectory.toPath());
        }
    }
    
    private int migrateDocumentsSequentiallyWithPostgres(
        FileSystemRepo sourceRepo,
        String snapshotName,
        List<String> indexAllowlist,
        SearchClusterContainer target,
        AtomicInteger runCounter,
        Random clockJitter,
        DocumentMigrationTestContext testContext,
        Version sourceVersion,
        Version targetVersion,
        String transformationConfig,
        PostgresConfig postgresConfig
    ) {
        for (int runNumber = 1; ; ++runNumber) {
            try {
                var workResult = migrateDocumentsWithOneWorkerPostgres(
                    sourceRepo,
                    snapshotName,
                    null,
                    indexAllowlist,
                    target.getUrl(),
                    clockJitter,
                    testContext,
                    sourceVersion,
                    targetVersion,
                    transformationConfig,
                    postgresConfig
                );
                if (workResult == org.opensearch.migrations.bulkload.worker.CompletionStatus.NOTHING_DONE) {
                    return runNumber;
                } else {
                    runCounter.incrementAndGet();
                }
            } catch (org.opensearch.migrations.RfsMigrateDocuments.NoWorkLeftException e) {
                throw new ExpectedMigrationWorkTerminationException(e, runNumber);
            } catch (Exception e) {
                // Continue on exception to simulate worker recycling
            }
        }
    }
    
    @SneakyThrows
    private org.opensearch.migrations.bulkload.worker.CompletionStatus migrateDocumentsWithOneWorkerPostgres(
        org.opensearch.migrations.bulkload.common.SourceRepo sourceRepo,
        String snapshotName,
        String previousSnapshotName,
        List<String> indexAllowlist,
        String targetAddress,
        Random clockJitter,
        DocumentMigrationTestContext context,
        Version sourceVersion,
        Version targetVersion,
        String transformationConfig,
        PostgresConfig postgresConfig
    ) throws org.opensearch.migrations.RfsMigrateDocuments.NoWorkLeftException {
        var tempDir = java.nio.file.Files.createTempDirectory("opensearchMigrationReindexFromSnapshot_test_lucene");
        try (var processManager = new org.opensearch.migrations.bulkload.workcoordination.LeaseExpireTrigger(workItemId -> {})) {
            var sourceResourceProvider = ClusterProviderRegistry.getSnapshotReader(sourceVersion, sourceRepo, false);
            var repoAccessor = new org.opensearch.migrations.bulkload.common.DefaultSourceRepoAccessor(sourceRepo);
            var unpackerFactory = new org.opensearch.migrations.bulkload.common.SnapshotShardUnpacker.Factory(
                repoAccessor,
                tempDir,
                sourceResourceProvider.getBufferSizeInBytes()
            );
            
            var readerFactory = new org.opensearch.migrations.bulkload.lucene.LuceneIndexReader.Factory(sourceResourceProvider);
            var docTransformer = new org.opensearch.migrations.transform.TransformationLoader().getTransformerFactoryLoader(
                java.util.Optional.ofNullable(transformationConfig).orElse(
                    org.opensearch.migrations.RfsMigrateDocuments.DEFAULT_DOCUMENT_TRANSFORMATION_CONFIG
                ));
            
            var progressCursor = new java.util.concurrent.atomic.AtomicReference<org.opensearch.migrations.bulkload.worker.WorkItemCursor>();
            var coordinatorFactory = new org.opensearch.migrations.bulkload.workcoordination.WorkCoordinatorFactory(targetVersion);
            var connectionContext = ConnectionContextTestParams.builder()
                .host(targetAddress)
                .awsRegion("eu-west-1")
                .awsServiceSigningName("aoss")
                .build()
                .toConnectionContext();
            var workItemRef = new java.util.concurrent.atomic.AtomicReference<org.opensearch.migrations.bulkload.workcoordination.IWorkCoordinator.WorkItemAndDuration>();
            
            try (var workCoordinator = coordinatorFactory.getPostgres(
                    postgresConfig,
                    TOLERABLE_CLIENT_SERVER_CLOCK_DIFFERENCE_SECONDS,
                    java.util.UUID.randomUUID().toString(),
                    java.time.Clock.systemUTC(),
                    workItemRef::set
            )) {
                workCoordinator.setup(() -> null);
                var clientFactory = new OpenSearchClientFactory(connectionContext);
                return org.opensearch.migrations.RfsMigrateDocuments.run(
                    readerFactory,
                    new org.opensearch.migrations.bulkload.common.DocumentReindexer(clientFactory.determineVersionAndCreate(), 1000, Long.MAX_VALUE, 1, () -> docTransformer),
                    progressCursor,
                    workCoordinator,
                    java.time.Duration.ofMinutes(10),
                    processManager,
                    sourceResourceProvider.getIndexMetadata(),
                    snapshotName,
                    previousSnapshotName,
                    previousSnapshotName != null ? org.opensearch.migrations.bulkload.common.DeltaMode.UPDATES_AND_DELETES : null,
                    indexAllowlist,
                    sourceResourceProvider.getShardMetadata(),
                    unpackerFactory,
                    MAX_SHARD_SIZE_BYTES,
                    context,
                    new java.util.concurrent.atomic.AtomicReference<>(),
                    new org.opensearch.migrations.bulkload.workcoordination.WorkItemTimeProvider());
            }
        } finally {
            deleteTree(tempDir);
        }
    }
}
