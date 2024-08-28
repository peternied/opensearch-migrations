package org.opensearch.migrations.commands;


import org.opensearch.migrations.MetadataArgs;
import org.opensearch.migrations.cli.Clusters;
import org.opensearch.migrations.clusters.RemoteCluster;
import org.opensearch.migrations.clusters.SnapshotSource;
import org.opensearch.migrations.clusters.SourceCluster;
import org.opensearch.migrations.metadata.GlobalMetadataCreator;
import org.opensearch.migrations.metadata.tracing.RootMetadataMigrationContext;

import com.beust.jcommander.ParameterException;
import com.rfs.common.ClusterVersion;
import com.rfs.common.OpenSearchClient;
import com.rfs.transformers.TransformFunctions;
import com.rfs.transformers.Transformer;
import com.rfs.worker.IndexRunner;
import com.rfs.worker.MetadataRunner;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class Migrate {

    private static final int INVALID_PARAMETER_CODE = 999;
    private static final int UNEXPECTED_FAILURE_CODE = 888;
    private final MetadataArgs arguments;

    public Migrate(MetadataArgs arguments) {
        this.arguments = arguments;
    }

    public MigrateResult execute(RootMetadataMigrationContext context) {
        var migrateResult = MigrateResult.builder();
        log.atInfo().setMessage("Command line arguments {0}").addArgument(arguments::toString).log();
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
            return migrateResult.exitCode(INVALID_PARAMETER_CODE).build();
        }

        final String snapshotName = arguments.snapshotName;
        final int awarenessDimensionality = arguments.minNumberOfReplicas + 1;

        var clusters = new Clusters();
        migrateResult.clusters(clusters);
        SourceCluster sourceCluster = null;
        if (arguments.fileSystemRepoPath != null) {
            sourceCluster = new SnapshotSource(arguments.sourceVersion, arguments.fileSystemRepoPath);
        } else if (arguments.s3LocalDirPath != null) {
            sourceCluster = new SnapshotSource(arguments.sourceVersion, arguments.s3LocalDirPath, arguments.s3RepoUri, arguments.s3Region);
        } else {
            log.atError().setMessage("No valid source for migration").log();
            return migrateResult.exitCode(INVALID_PARAMETER_CODE).build();
        }
        clusters.setSource(sourceCluster);

        var targetCluster = new RemoteCluster(arguments.targetVersion, arguments.targetArgs.toConnectionContext());
        clusters.setTarget(targetCluster);

        try {

            log.info("Running RfsWorker");
            OpenSearchClient targetClient = new OpenSearchClient(arguments.targetArgs.toConnectionContext());

            
            final GlobalMetadataCreator metadataCreator = targetCluster.getGlobalMetadataCreator(
                arguments.dataFilterArgs,
                context.createMetadataMigrationContext()
            );
            final Transformer transformer = TransformFunctions.getTransformer(
                ClusterVersion.fromVersion(sourceCluster.getVersion()),
                ClusterVersion.fromVersion(targetCluster.getVersion()),
                awarenessDimensionality
            );
            new MetadataRunner(snapshotName, sourceCluster.getMetadata(), metadataCreator, transformer).migrateMetadata();
            log.info("Metadata copy complete.");

            new IndexRunner(
                snapshotName,
                sourceCluster.getIndexMetadata(),
                targetCluster.getIndexCreator(),
                transformer,
                arguments.dataFilterArgs.indexAllowlist,
                context.createIndexContext()
            ).migrateIndices();
            log.info("Index copy complete.");
        } catch (Exception e) {
            log.atError().setMessage("Unexpected failure").setCause(e).log();
            migrateResult.exitCode(UNEXPECTED_FAILURE_CODE);
        }

        return migrateResult.build();
    }
}
