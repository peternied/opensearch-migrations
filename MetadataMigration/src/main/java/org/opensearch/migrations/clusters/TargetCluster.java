package org.opensearch.migrations.clusters;

import org.opensearch.migrations.cli.Printable;
import org.opensearch.migrations.cli.Printer;
import org.opensearch.migrations.cli.Validate;

import lombok.AllArgsConstructor;
import lombok.Builder;

@Builder
@AllArgsConstructor
public class TargetCluster implements Printable, Validate {
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

    @Override
    public boolean validate() {
        return true;
    }
}