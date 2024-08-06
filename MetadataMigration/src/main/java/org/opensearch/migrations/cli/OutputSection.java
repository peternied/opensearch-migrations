package org.opensearch.migrations.cli;

import java.util.List;
import java.util.Map;
import static java.util.Map.entry;
import lombok.Builder;
import lombok.Singular;

@Builder
public class OutputSection {
    public final String section;
    @Singular(ignoreNullCollections = true)
    public List<Printable> entries;
    @Singular(ignoreNullCollections = true)
    public List<Map.Entry<String, String>> fields;
    @Singular(ignoreNullCollections = true)
    public List<Message> messages;

    static {
        OutputSection.builder().field(entry("null", "null")).build();
    }
}