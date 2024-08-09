package org.opensearch.migrations.clusters;

import java.util.List;

import org.opensearch.migrations.DataFiltersArgs;
import org.opensearch.migrations.Version;
import org.opensearch.migrations.cli.Printer;
import org.opensearch.migrations.metadata.GlobalMetadataCreator;
import org.opensearch.migrations.metadata.tracing.IMetadataMigrationContexts.IClusterMetadataContext;

import lombok.AllArgsConstructor;
import lombok.Builder;

import com.rfs.common.http.ConnectionContext;
import com.rfs.models.GlobalMetadata.Factory;

@AllArgsConstructor
public class RemoteCluster implements TargetCluster {
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
        
        throw new UnsupportedOperationException("Unimplemented method 'getGlobalMetadataCreator'");
    }
}