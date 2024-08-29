package org.opensearch.migrations.cli;

import org.opensearch.migrations.clusters.SourceCluster;
import org.opensearch.migrations.clusters.TargetCluster;

import lombok.Builder;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

@Slf4j
@Getter
@Builder
public class Clusters {
    private SourceCluster source;
    private TargetCluster target;

    public String toString() {
        var sb = new StringBuilder();
        sb.append("Clusters:" + System.lineSeparator());
        if (getSource() != null) {
            sb.append("   Source:" + System.lineSeparator());
            sb.append("      " + getSource() + System.lineSeparator());
            sb.append(System.lineSeparator());
        }
        if (getTarget() != null) {
            sb.append("   Target:" + System.lineSeparator());
            sb.append("      " + getTarget() + System.lineSeparator());
            sb.append(System.lineSeparator());
        }
        return sb.toString();
    }
}
