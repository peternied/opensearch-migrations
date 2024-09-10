package org.opensearch.migrations;

import java.io.File;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Stream;

import org.hamcrest.Matchers;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.ArgumentsSource;
import org.junit.jupiter.params.provider.EnumSource;
import org.junit.jupiter.params.provider.MethodSource;
import org.opensearch.migrations.commands.MigrationItemResult;
import org.opensearch.migrations.metadata.tracing.MetadataMigrationTestContext;
import org.opensearch.migrations.snapshot.creation.tracing.SnapshotTestContext;

import com.rfs.common.FileSystemSnapshotCreator;
import com.rfs.common.OpenSearchClient;
import com.rfs.common.http.ConnectionContextTestParams;
import com.rfs.framework.SearchClusterContainer;
import com.rfs.http.ClusterOperations;
import com.rfs.models.DataFilterArgs;
import com.rfs.worker.SnapshotRunner;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;

import static org.hamcrest.CoreMatchers.equalTo;
import static org.hamcrest.MatcherAssert.assertThat;

/**
 * Tests focused on setting up whole source clusters, performing a migration, and validation on the target cluster
 */
@Tag("longTest")
@Slf4j
class EndToEndTest {

    @TempDir
    private File localDirectory;

    private static Stream<Arguments> scenarios() {
        return Stream.of(
            Arguments.of(TransferMedium.Http, MetadataCommands.Evaluate),
            Arguments.of(TransferMedium.SnapshotImage, MetadataCommands.Migrate),
            Arguments.of(TransferMedium.Http, MetadataCommands.Migrate)
        );
    }

    @ParameterizedTest(name = "Command {1}, Medium of transfer {0}")
    @MethodSource(value = "scenarios")
    void metadataMigrateFrom_ES_v6_8(TransferMedium medium, MetadataCommands command) throws Exception {
        try (
            final var sourceCluster = new SearchClusterContainer(SearchClusterContainer.ES_V6_8_23);
            final var targetCluster = new SearchClusterContainer(SearchClusterContainer.OS_V2_14_0)
        ) {
            migrateFrom_ES(sourceCluster, targetCluster, medium, command);
        }
    }

    @ParameterizedTest(name = "Command {1}, Medium of transfer {0}")
    @MethodSource(value = "scenarios")
    void metadataMigrateFrom_ES_v7_17(TransferMedium medium, MetadataCommands command) throws Exception {
        try (
            final var sourceCluster = new SearchClusterContainer(SearchClusterContainer.ES_V7_17);
            final var targetCluster = new SearchClusterContainer(SearchClusterContainer.OS_V2_14_0)
        ) {
            migrateFrom_ES(sourceCluster, targetCluster, medium, command);
        }
    }

    @ParameterizedTest(name = "Command {1}, Medium of transfer {0}")
    @MethodSource(value = "scenarios")
    void metadataMigrateFrom_ES_v7_10(TransferMedium medium, MetadataCommands command) throws Exception {
        try (
            final var sourceCluster = new SearchClusterContainer(SearchClusterContainer.ES_V7_10_2);
            final var targetCluster = new SearchClusterContainer(SearchClusterContainer.OS_V2_14_0)
        ) {
            migrateFrom_ES(sourceCluster, targetCluster, medium, command);
        }
    }

    @ParameterizedTest(name = "Command {1}, Medium of transfer {0}")
    @MethodSource(value = "scenarios")
    void metadataMigrateFrom_OS_v1_3(TransferMedium medium, MetadataCommands command) throws Exception {
        try (
            final var sourceCluster = new SearchClusterContainer(SearchClusterContainer.OS_V1_3_16);
            final var targetCluster = new SearchClusterContainer(SearchClusterContainer.OS_V2_14_0)
        ) {
            migrateFrom_ES(sourceCluster, targetCluster, medium, command);
        }
    }

    private enum TransferMedium {
        SnapshotImage,
        Http
    }

    @SneakyThrows
    private void migrateFrom_ES(
        final SearchClusterContainer sourceCluster,
        final SearchClusterContainer targetCluster,
        final TransferMedium medium,
        final MetadataCommands command
    ) {
        // ACTION: Set up the source/target clusters
        var bothClustersStarted = CompletableFuture.allOf(
            CompletableFuture.runAsync(() -> sourceCluster.start()),
            CompletableFuture.runAsync(() -> targetCluster.start())
        );
        bothClustersStarted.join();

        Version sourceVersion = sourceCluster.getContainerVersion().getVersion();
        var sourceIsES6_8 = VersionMatchers.isES_6_8.test(sourceVersion);
        var sourceIsES7_X = VersionMatchers.isES_7_X.test(sourceVersion) || VersionMatchers.isOS_1_X.test(sourceVersion);

        if (!(sourceIsES6_8 || sourceIsES7_X)) {
            throw new RuntimeException("This test cannot handle the source cluster version" + sourceVersion);
        }

        // Create the component and index templates
        var sourceClusterOperations = new ClusterOperations(sourceCluster.getUrl());
        var compoTemplateName = "simple_component_template";
        var indexTemplateName = "simple_index_template";
        if (sourceIsES7_X) {
            sourceClusterOperations.createES7Templates(compoTemplateName, indexTemplateName, "author", "blog*");
        } else if (sourceIsES6_8) {
            sourceClusterOperations.createES6LegacyTemplate(indexTemplateName, "movies*");
        }

        // Creates a document that uses the template
        var blogIndexName = "blog_2023";
        sourceClusterOperations.createDocument(blogIndexName, "222", "{\"author\":\"Tobias Funke\"}");
        var movieIndexName = "movies_2023";
        sourceClusterOperations.createDocument(movieIndexName,"123", "{\"title\":\"This is spinal tap\"}");

        var arguments = new MetadataArgs();

        switch (medium) {
            case SnapshotImage:
                var snapshotContext = SnapshotTestContext.factory().noOtelTracking();
                var snapshotName = "my_snap";
                log.info("Source cluster {}", sourceCluster.getUrl());
                var sourceClient = new OpenSearchClient(ConnectionContextTestParams.builder()
                    .host(sourceCluster.getUrl())
                    .insecure(true)
                    .build()
                    .toConnectionContext());
                var snapshotCreator = new FileSystemSnapshotCreator(
                    snapshotName,
                    sourceClient,
                    SearchClusterContainer.CLUSTER_SNAPSHOT_DIR,
                    snapshotContext.createSnapshotCreateContext()
                );
                SnapshotRunner.runAndWaitForCompletion(snapshotCreator);
                sourceCluster.copySnapshotData(localDirectory.toString());
                arguments.fileSystemRepoPath = localDirectory.getAbsolutePath();
                arguments.snapshotName = snapshotName;
                arguments.sourceVersion = sourceVersion;
                break;
        
            case Http:
                arguments.sourceArgs.host = sourceCluster.getUrl();
                break;
        }

        arguments.targetArgs.host = targetCluster.getUrl();

        var dataFilterArgs = new DataFilterArgs();
        dataFilterArgs.indexAllowlist = List.of(blogIndexName, movieIndexName);
        dataFilterArgs.componentTemplateAllowlist = List.of(compoTemplateName);
        dataFilterArgs.indexTemplateAllowlist = List.of(indexTemplateName);
        arguments.dataFilterArgs = dataFilterArgs;


        // ACTION: Migrate the templates
        var metadataContext = MetadataMigrationTestContext.factory().noOtelTracking();
        var metadata = new MetadataMigration(arguments);
        
        MigrationItemResult result;
        int expectedResponseCode;
        if (MetadataCommands.Evaluate.equals(command)) {
            result = metadata.evaluate().execute(metadataContext);
            expectedResponseCode = 404;
        } else if (MetadataCommands.Migrate.equals(command)) {
            result = metadata.migrate().execute(metadataContext);
            expectedResponseCode = 200;
        } else {
            throw new RuntimeException("Unexpected command " + command);
        }

        log.info(result.toString());
        assertThat(result.getExitCode(), equalTo(0));

        // Check that the index was migrated
        var targetClusterOperations = new ClusterOperations(targetCluster.getUrl());
        var res = targetClusterOperations.get("/" + blogIndexName);
        assertThat(res.getValue(), res.getKey(), equalTo(expectedResponseCode));

        res = targetClusterOperations.get("/" + movieIndexName);
        assertThat(res.getValue(), res.getKey(), equalTo(expectedResponseCode));
        
        // Check that the templates were migrated
        if (sourceIsES7_X) {
            res = targetClusterOperations.get("/_index_template/" + indexTemplateName);
            assertThat(res.getValue(), res.getKey(), equalTo(expectedResponseCode));
        } else if (sourceIsES6_8) {
            res = targetClusterOperations.get("/_template/" + indexTemplateName);
            assertThat(res.getValue(), res.getKey(), equalTo(expectedResponseCode));
        }
    }
}
