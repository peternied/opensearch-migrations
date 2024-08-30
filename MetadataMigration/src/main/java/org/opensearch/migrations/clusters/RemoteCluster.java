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
import org.opensearch.migrations.metadata.tracing.RootMetadataMigrationContext;

import com.rfs.common.OpenSearchClient;
import com.rfs.common.http.ConnectionContext;
import com.rfs.models.GlobalMetadata.Factory;
import com.rfs.version_os_2_11.GlobalMetadataCreator_OS_2_11;
import com.rfs.version_os_2_11.IndexCreator_OS_2_11;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.ToString;

@RequiredArgsConstructor
@ToString(onlyExplicitlyIncluded = true)
public class RemoteCluster implements TargetCluster, SourceCluster {
    private final Version OS_2_X = Version.builder().flavor(Flavor.OpenSearch).major(2).build();
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

    @Override
    public GlobalMetadataCreator getGlobalMetadataCreator(
        DataFiltersArgs dataFilters
    ) {
        if (VersionMatchers.isOpenSearch_2_X.apply(getVersion())) {
            return new GlobalMetadataCreator_OS_2_11(new OpenSearchClient(connection), null, dataFilters.componentTemplateAllowlist, dataFilters.indexTemplateAllowlist, metadataContext.createMetadataMigrationContext());
        }

        throw new UnsupportedOperationException("Unimplemented method 'getGlobalMetadataCreator'" + getVersion());
    }

    @Override
    public IndexCreator getIndexCreator() {
        if (VersionMatchers.isOpenSearch_2_X.apply(getVersion())) {
            return new IndexCreator_OS_2_11(new OpenSearchClient(connection), metadataContext.createIndexContext());
        }

        throw new UnsupportedOperationException("Unimplemented method 'getIndexCreator'" + getVersion());
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
