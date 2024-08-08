package org.opensearch.migrations.clusters;

import org.opensearch.migrations.cli.Printer;

import lombok.Builder;

import com.rfs.common.http.ConnectionContext;

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
}