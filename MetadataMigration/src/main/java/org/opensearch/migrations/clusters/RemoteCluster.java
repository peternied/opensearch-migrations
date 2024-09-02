package org.opensearch.migrations.clusters;



import org.opensearch.migrations.DataFiltersArgs;
import org.opensearch.migrations.Version;
import org.opensearch.migrations.VersionMatchers;
import org.opensearch.migrations.metadata.GlobalMetadataCreator;
import org.opensearch.migrations.metadata.IndexCreator;
import org.opensearch.migrations.metadata.tracing.RootMetadataMigrationContext;

import com.rfs.common.OpenSearchClient;
import com.rfs.common.http.ConnectionContext;
import com.rfs.models.GlobalMetadata;
import com.rfs.models.IndexMetadata;
import com.rfs.version_os_2_11.GlobalMetadataCreator_OS_2_11;
import com.rfs.version_os_2_11.IndexCreator_OS_2_11;
import com.rfs.version_remote.RemoteIndexMetadataFactory;
import com.rfs.version_remote.RemoteMetadataFactory;
import lombok.RequiredArgsConstructor;
import lombok.ToString;

@RequiredArgsConstructor
@ToString(onlyExplicitlyIncluded = true)
public class RemoteCluster implements TargetCluster, SourceCluster {
    @ToString.Include
    private final ConnectionContext connection;
    private final RootMetadataMigrationContext metadataContext;
    private Version version = null;

    @ToString.Include
    public Version getVersion() {
        if (version == null) {
            version = new OpenSearchClient(connection).getClusterVersion();
        }
        return version;
    }

    @Override
    public GlobalMetadataCreator getGlobalMetadataCreator(
        DataFiltersArgs dataFilters
    ) {
        if (VersionMatchers.isOpenSearch_2_X.test(getVersion())) {
            return new GlobalMetadataCreator_OS_2_11(new OpenSearchClient(connection), dataFilters.indexTemplateAllowlist, dataFilters.componentTemplateAllowlist, dataFilters.indexTemplateAllowlist, metadataContext.createMetadataMigrationContext());
        }

        throw new UnsupportedOperationException("Unimplemented method 'getGlobalMetadataCreator'" + getVersion());
    }

    @Override
    public IndexCreator getIndexCreator() {
        if (VersionMatchers.isOpenSearch_2_X.test(getVersion())) {
            return new IndexCreator_OS_2_11(new OpenSearchClient(connection), metadataContext.createIndexContext());
        }

        throw new UnsupportedOperationException("Unimplemented method 'getIndexCreator'" + getVersion());
    }

    @Override
    public GlobalMetadata.Factory getMetadata() {
        return new RemoteMetadataFactory(new OpenSearchClient(connection));
    }

    @Override
    public IndexMetadata.Factory getIndexMetadata() {
        return new RemoteIndexMetadataFactory(new OpenSearchClient(connection));
    }
}
