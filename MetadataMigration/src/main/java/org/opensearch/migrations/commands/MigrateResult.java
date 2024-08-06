package org.opensearch.migrations.commands;

import org.opensearch.migrations.cli.Clusters;

import lombok.Builder;
import lombok.Getter;

@Builder
@Getter
public class MigrateResult implements Result {
    private final Clusters clusters;
    private final int exitCode;
}
