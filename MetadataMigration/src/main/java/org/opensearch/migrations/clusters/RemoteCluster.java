package org.opensearch.migrations.clusters;

import org.opensearch.migrations.Version;
import org.opensearch.migrations.cli.Printer;

import lombok.Builder;

import com.rfs.common.http.ConnectionContext;
import com.rfs.models.GlobalMetadata.Factory;

public class RemoteCluster implements SourceCluster {
    private final ConnectionContext connection;
    private String flavor;
    private int version;

    public RemoteCluster(ConnectionContext connection) {
        this.connection = connection;
    }

    public Printer asPrinter() {
        return Printer.builder()
            .section("Target Cluster")
            .field("Version", flavor + " " + version)
            .field("Url", connection.toString())
            .build();
    }

    @Override
    public Version getVersion() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getVersion'");
    }

    @Override
    public Factory getMetadata() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getMetadata'");
    }

    @Override
    public com.rfs.models.IndexMetadata.Factory getIndexMetadata() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getIndexMetadata'");
    }
}