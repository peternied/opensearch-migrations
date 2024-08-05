package org.opensearch.migrations.cli;

import org.slf4j.event.Level;

import lombok.Builder;
import lombok.Getter;

@Builder(builderMethodName = "Builder")
@Getter
public class Message {
    private final Level level;
    private final String body;
}
