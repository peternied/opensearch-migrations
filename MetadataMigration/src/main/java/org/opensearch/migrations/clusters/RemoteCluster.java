package org.opensearch.migrations.clusters;


import java.util.List;
import java.util.function.Function;
import java.util.function.Predicate;

import org.opensearch.migrations.DataFiltersArgs;
import org.opensearch.migrations.Flavor;
import org.opensearch.migrations.Version;
import org.opensearch.migrations.VersionMatchers;
import org.opensearch.migrations.metadata.GlobalMetadataCreator;
import org.opensearch.migrations.metadata.IndexCreator;
import org.opensearch.migrations.metadata.tracing.IMetadataMigrationContexts.ICreateIndexContext;
import org.opensearch.migrations.metadata.tracing.IMetadataMigrationContexts.IClusterMetadataContext;
import org.opensearch.migrations.metadata.tracing.RootMetadataMigrationContext;

import com.rfs.common.OpenSearchClient;
import com.rfs.common.http.ConnectionContext;
import com.rfs.models.GlobalMetadata.Factory;
import com.rfs.version_os_2_11.GlobalMetadataCreator_OS_2_11;
import com.rfs.version_os_2_11.IndexCreator_OS_2_11;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.AllArgsConstructor;
import lombok.RequiredArgsConstructor;
import lombok.ToString;

@RequiredArgsConstructor
@ToString(onlyExplicitlyIncluded = true)
public class RemoteCluster implements TargetCluster, SourceCluster {

    private static final List<Provider> registeredProviders = List.of(
        new Provider(
            VersionMatchers.isOpenSearch_2_X,
            args -> new GlobalMetadataCreator_OS_2_11(args.client, args.dataFiltersArgs.indexTemplateAllowlist, args.dataFiltersArgs.componentTemplateAllowlist, args.dataFiltersArgs.indexTemplateAllowlist, args.context),
            args -> new IndexCreator_OS_2_11(args.client, args.context)
        )
    );

    @AllArgsConstructor
    private static class Provider {
        Predicate<Version> applies;
        Function<GlobalMetadataArgs, GlobalMetadataCreator> globalMetadataCreator;
        Function<IndexCreatorArgs, IndexCreator> indexCreator;
    }

    @AllArgsConstructor
    private static class GlobalMetadataArgs {
        OpenSearchClient client;
        DataFiltersArgs dataFiltersArgs;
        IClusterMetadataContext context;
    }

    @AllArgsConstructor
    private static class IndexCreatorArgs {
        OpenSearchClient client;
        ICreateIndexContext context;
    }


    @ToString.Include
    private final ConnectionContext connection;
    private final RootMetadataMigrationContext metadataContext;
    private Version version = null;

    public Version getVersion() {
        if (version == null) {
            version = new OpenSearchClient(connection).getClusterVersion(null);
        }
        return version;
    }

    private Provider getMatchingProvider() {
        return registeredProviders.stream()
            .filter(p -> p.applies.test(getVersion()))
            .findFirst()
            .orElseThrow(() -> new UnsupportedOperationException("Unable to find provider for version " + getVersion()));
    }

    @Override
    public GlobalMetadataCreator getGlobalMetadataCreator(
        DataFiltersArgs dataFilters
    ) {
        return getMatchingProvider().globalMetadataCreator.apply(new GlobalMetadataArgs(new OpenSearchClient(connection), dataFilters, metadataContext.createMetadataMigrationContext()));
    }

    @Override
    public IndexCreator getIndexCreator() {
        return getMatchingProvider().indexCreator.apply(new IndexCreatorArgs(new OpenSearchClient(connection), metadataContext.createIndexContext()));
    }

    @Override
    public Factory getMetadata() {
        throw new UnsupportedOperationException("Unimplemented method 'getMetadata'");
    }

    @Override
    public com.rfs.models.IndexMetadata.Factory getIndexMetadata() {
        throw new UnsupportedOperationException("Unimplemented method 'getIndexMetadata'");
    }

}
