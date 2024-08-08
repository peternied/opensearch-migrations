package org.opensearch.migrations.clusters;

import org.opensearch.migrations.cli.Printer;

import lombok.AllArgsConstructor;
import lombok.Builder;

@Builder
@AllArgsConstructor
public class RemoteCluster implements SourceCluster {
    private String url;
    private String flavor;
    private int version;

    public Printer asPrinter() {
        return Printer.builder()
            .section("Target Cluster")
            .field("Version", flavor + " " + version)
            .field("Url", url)
            .build();
    }
}