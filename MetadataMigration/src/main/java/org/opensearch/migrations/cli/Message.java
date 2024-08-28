package org.opensearch.migrations.cli;

import lombok.Builder;
import lombok.Getter;
import org.slf4j.event.Level;

@Builder(builderMethodName = "Builder")
@Getter
public class Message {
    private final Level level;
    private final String body;
}
