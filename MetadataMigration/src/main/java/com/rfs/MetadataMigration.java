package com.rfs;

import com.beust.jcommander.JCommander;
import com.beust.jcommander.Parameter;
import com.beust.jcommander.ParametersDelegate;

import java.util.List;

import com.rfs.common.ClusterVersion;
import com.rfs.common.ConnectionDetails;
import com.rfs.common.GlobalMetadata;
import com.rfs.common.IndexMetadata;
import com.rfs.common.OpenSearchClient;
import com.rfs.common.SnapshotRepo;
import com.rfs.common.SourceRepo;
import com.rfs.transformers.TransformFunctions;
import com.rfs.transformers.Transformer;
import com.rfs.version_es_7_10.GlobalMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.IndexMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.SnapshotRepoProvider_ES_7_10;
import com.rfs.version_os_2_11.GlobalMetadataCreator_OS_2_11;
import com.rfs.version_os_2_11.IndexCreator_OS_2_11;
import com.rfs.worker.IndexRunner;
import com.rfs.worker.MetadataRunner;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class MetadataMigration {

    public static class Args {
        @Parameter(names = {"--snapshot-name"}, description = "The name of the snapshot to migrate", required = true)
        public String snapshotName;

        @ParametersDelegate
        public SourceRepo.Params sourceRepo;

        @ParametersDelegate
        public ConnectionDetails.TargetArgs targetArgs;
        
        @Parameter(names = {"--index-allowlist"}, description = ("Optional.  List of index names to migrate"
            + " (e.g. 'logs_2024_01, logs_2024_02').  Default: all non-system indices (e.g. those not starting with '.')"), required = false)
        public List<String> indexAllowlist = List.of();

        @Parameter(names = {"--index-template-allowlist"}, description = ("Optional.  List of index template names to migrate"
            + " (e.g. 'posts_index_template1, posts_index_template2').  Default: empty list"), required = false)
        public List<String> indexTemplateAllowlist = List.of();

        @Parameter(names = {"--component-template-allowlist"}, description = ("Optional. List of component template names to migrate"
            + " (e.g. 'posts_template1, posts_template2').  Default: empty list"), required = false)
        public List<String> componentTemplateAllowlist = List.of();
        
        //https://opensearch.org/docs/2.11/api-reference/cluster-api/cluster-awareness/
        @Parameter(names = {"--min-replicas"}, description = ("Optional.  The minimum number of replicas configured for migrated indices on the target."
            + " This can be useful for migrating to targets which use zonal deployments and require additional replicas to meet zone requirements.  Default: 0")
            , required = false)
        public int minNumberOfReplicas = 0;
    }

    public static void main(String[] args) throws Exception {
        // Grab out args
        Args arguments = new Args();
        JCommander.newBuilder()
                .addObject(arguments)
                .build()
                .parse(args);

        final List<String> indexAllowlist = arguments.indexAllowlist;
        final List<String> indexTemplateAllowlist = arguments.indexTemplateAllowlist;
        final List<String> componentTemplateAllowlist = arguments.componentTemplateAllowlist;
        final int awarenessDimensionality = arguments.minNumberOfReplicas + 1;

        final ConnectionDetails targetConnection = new ConnectionDetails(arguments.targetArgs);


        log.info("Running RfsWorker");
        OpenSearchClient targetClient = new OpenSearchClient(targetConnection);

        final SnapshotRepo.Provider repoDataProvider = new SnapshotRepoProvider_ES_7_10(arguments.sourceRepo.getRepo());
        final GlobalMetadata.Factory metadataFactory = new GlobalMetadataFactory_ES_7_10(repoDataProvider);
        final GlobalMetadataCreator_OS_2_11 metadataCreator = new GlobalMetadataCreator_OS_2_11(targetClient, List.of(), componentTemplateAllowlist, indexTemplateAllowlist);
        final Transformer transformer = TransformFunctions.getTransformer(ClusterVersion.ES_7_10, ClusterVersion.OS_2_11, awarenessDimensionality);
        new MetadataRunner(arguments.snapshotName, metadataFactory, metadataCreator, transformer).migrateMetadata();

        final IndexMetadata.Factory indexMetadataFactory = new IndexMetadataFactory_ES_7_10(repoDataProvider);
        final IndexCreator_OS_2_11 indexCreator = new IndexCreator_OS_2_11(targetClient);
        new IndexRunner(arguments.snapshotName, indexMetadataFactory, indexCreator, transformer, indexAllowlist).migrateIndices();
    }
}
