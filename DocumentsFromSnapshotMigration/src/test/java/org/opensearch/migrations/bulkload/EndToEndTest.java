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
import org.opensearch.migrations.cluster.ClusterProviderRegistry;
import org.opensearch.migrations.reindexer.tracing.DocumentMigrationTestContext;
import org.opensearch.migrations.snapshot.creation.tracing.SnapshotTestContext;

import lombok.SneakyThrows;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.io.TempDir;
import org.mockito.Mockito;
import org.testcontainers.lifecycle.Startables;

@Tag("isolatedTest")
public class EndToEndTest extends SourceTestBase {
    @TempDir
    private File localDirectory;
    
    private static final String SERVERLESS_ENDPOINT = "https://aurfb38nmcwqqqf7zmxj.eu-west-1.aoss.amazonaws.com";

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
            var expectedTerminationException = waitForRfsCompletion(() -> migrateDocumentsSequentially(
                    sourceRepo,
                    snapshotName,
                    List.of(),
                    mockTargetCluster,
                    runCounter,
                    clockJitter,
                    testDocMigrationContext,
                    sourceCluster.getContainerVersion().getVersion(),
                    mockTargetCluster.getContainerVersion().getVersion(),
                    null
            ));

            Assertions.assertTrue(expectedTerminationException.numRuns > 0);
            System.out.println("Migration to serverless completed successfully with " + expectedTerminationException.numRuns + " runs");
        } finally {
            deleteTree(localDirectory.toPath());
        }
    }
}
