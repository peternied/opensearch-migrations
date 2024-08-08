package org.opensearch.migrations.clusters;

import org.opensearch.migrations.cli.Printer;

import lombok.Builder;

@Builder
public class HostSource {

    private final String url;
    private final String flavor;
    private final int version;

    public Printer asPrinter() {
        return Printer.builder()
            .section("Cluster")
            .field("Version", flavor + " " + version)
            .field("Url", url)
            .build();
    }

    public boolean isAvailable() {
        return true;
    }

    public boolean validate() {
        return true;
    }
}
