package org.opensearch.migrations.clusters;


import org.opensearch.migrations.DataFiltersArgs;
import org.opensearch.migrations.Flavor;
import org.opensearch.migrations.Version;
import org.opensearch.migrations.cli.Printer;
import org.opensearch.migrations.metadata.GlobalMetadataCreator;
import org.opensearch.migrations.metadata.IndexCreator;
import org.opensearch.migrations.metadata.tracing.IMetadataMigrationContexts.IClusterMetadataContext;

import com.rfs.common.OpenSearchClient;
import com.rfs.common.http.ConnectionContext;
import com.rfs.version_os_2_11.GlobalMetadataCreator_OS_2_11;
import com.rfs.version_os_2_11.IndexCreator_OS_2_11;
import lombok.AllArgsConstructor;

@AllArgsConstructor
public class RemoteCluster implements TargetCluster {
    private final Version OS_2_X = Version.builder().flavor(Flavor.OpenSearch).major(2).build();
    private final Version version;
    private final ConnectionContext connection;

    public Printer asPrinter() {
        return Printer.builder()
            .section("Target Cluster")
            .field("Version", version.toString())
            .field("Url", connection.toString())
            .build();
    }

    public Version getVersion() {
        return version;
    }

    @Override
    public GlobalMetadataCreator getGlobalMetadataCreator(
        DataFiltersArgs dataFilters,
        IClusterMetadataContext context
    ) {
        if (version.matches(OS_2_X)) {
            return new GlobalMetadataCreator_OS_2_11(new OpenSearchClient(connection), null, dataFilters.componentTemplateAllowlist, dataFilters.indexTemplateAllowlist, context);
        }

        throw new UnsupportedOperationException("Unimplemented method 'getGlobalMetadataCreator'" + version);
    }

    @Override
    public IndexCreator getIndexCreator() {
        if (version.equals(Version.builder().flavor(Flavor.OpenSearch).major(2).minor(11).build())) {
            return new IndexCreator_OS_2_11(new OpenSearchClient(connection));
        }

        throw new UnsupportedOperationException("Unimplemented method 'getIndexCreator'" + version);
    }
}
