package org.opensearch.migrations.commands;


import java.util.ArrayList;

import org.opensearch.migrations.MetadataArgs;
import org.opensearch.migrations.cli.Clusters;
import org.opensearch.migrations.cli.Items;
import org.opensearch.migrations.clusters.RemoteCluster;
import org.opensearch.migrations.clusters.SnapshotSource;
import org.opensearch.migrations.clusters.SourceCluster;
import org.opensearch.migrations.metadata.tracing.RootMetadataMigrationContext;

import com.beust.jcommander.ParameterException;
import com.rfs.transformers.TransformFunctions;
import com.rfs.worker.IndexRunner;
import com.rfs.worker.MetadataRunner;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class Migrate {

    static final int INVALID_PARAMETER_CODE = 999;
    static final int UNEXPECTED_FAILURE_CODE = 888;
    private final MetadataArgs arguments;

    public Migrate(MetadataArgs arguments) {
        this.arguments = arguments;
    }

    public MigrateResult execute(RootMetadataMigrationContext context) {
        var migrateResult = MigrateResult.builder();
        log.atInfo().setMessage("Command line arguments {0}").addArgument(arguments::toString).log();

        if (arguments.sourceArgs == null || arguments.sourceArgs.host == null) {
            try {
                if (arguments.fileSystemRepoPath == null && arguments.s3RepoUri == null) {
                    throw new ParameterException("Either file-system-repo-path or s3-repo-uri must be set");
                }
                if (arguments.fileSystemRepoPath != null && arguments.s3RepoUri != null) {
                    throw new ParameterException("Only one of file-system-repo-path and s3-repo-uri can be set");
                }
                if ((arguments.s3RepoUri != null) && (arguments.s3Region == null || arguments.s3LocalDirPath == null)) {
                    throw new ParameterException("If an s3 repo is being used, s3-region and s3-local-dir-path must be set");
                } 
            } catch (Exception e) {
                log.atError().setMessage("Invalid parameter").setCause(e).log();
                return migrateResult
                    .exitCode(INVALID_PARAMETER_CODE)
                    .errorMessage("Invalid parameter: " + e.getMessage())
                    .build();
            }
        }

        final String snapshotName = arguments.snapshotName;
        final int awarenessDimensionality = arguments.minNumberOfReplicas + 1;

        SourceCluster sourceCluster = null;
        if (arguments.sourceArgs != null && arguments.sourceArgs.host != null) {
            sourceCluster = new RemoteCluster(arguments.sourceArgs.toConnectionContext(), context);
        } else if (arguments.fileSystemRepoPath != null) {
            sourceCluster = new SnapshotSource(arguments.sourceVersion, arguments.fileSystemRepoPath);
        } else if (arguments.s3LocalDirPath != null) {
            sourceCluster = new SnapshotSource(arguments.sourceVersion, arguments.s3LocalDirPath, arguments.s3RepoUri, arguments.s3Region);
        } else {
            log.atError().setMessage("No valid source for migration").log();
            return migrateResult
                .exitCode(INVALID_PARAMETER_CODE)
                .errorMessage("No valid source for migration")
                .build();
        }
        var clusters = Clusters.builder();
        clusters.source(sourceCluster);

        var targetCluster = new RemoteCluster(arguments.targetArgs.toConnectionContext(), context);
        clusters.target(targetCluster);

        try {
            log.info("Running Metadata worker");
            
            var metadataCreator = targetCluster.getGlobalMetadataCreator(arguments.dataFilterArgs);
            var transformer = TransformFunctions.getTransformer(
                sourceCluster.getVersion(),
                targetCluster.getVersion(),
                awarenessDimensionality
            );
            var metadataResults = new MetadataRunner(snapshotName, sourceCluster.getMetadata(), metadataCreator, transformer).migrateMetadata();
            var items = Items.builder();
            var indexTemplates = new ArrayList<String>();
            indexTemplates.addAll(metadataResults.getLegacyTemplates());
            indexTemplates.addAll(metadataResults.getIndexTemplates());
            items.indexTemplates(indexTemplates);
            items.componentTemplates(metadataResults.getComponentTemplates());

            log.info("Metadata copy complete.");

            var indexes = new IndexRunner(
                snapshotName,
                sourceCluster.getIndexMetadata(),
                targetCluster.getIndexCreator(),
                transformer,
                arguments.dataFilterArgs.indexAllowlist
            ).migrateIndices();
            items.indexes(indexes);
            migrateResult.items(items.build());
            log.info("Index copy complete.");
        } catch (Throwable e) {
            log.atError().setMessage("Unexpected failure").setCause(e).log();
            migrateResult
                .exitCode(UNEXPECTED_FAILURE_CODE)
                .errorMessage("Unexpected failure: " + e.getMessage())
                .build();
        }

        migrateResult.clusters(clusters.build());
        return migrateResult.build();
    }
}
