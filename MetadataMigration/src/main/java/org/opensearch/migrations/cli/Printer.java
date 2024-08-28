package org.opensearch.migrations.cli;

import java.util.Arrays;
import java.util.List;
import java.util.Map;

import lombok.AccessLevel;
import lombok.Builder;
import lombok.Singular;

@Builder(builderClassName = "Builder", access = AccessLevel.PUBLIC)
public class Printer {
    private static final int LEVEL_SPACER_AMOUNT = 3; 
    private static final String SPACER = " "; 
    private static final String SECTION_ENDING = ":"; 
    private static final String SECTION_SPACER = " "; 

    public final String section;
    @Singular
    public List<Object> entries;
    @Singular
    public Map<String, String> fields;
    @Singular
    public List<Message> messages;

    public String prettyPrint(int level) {
        var topIntentLevel = SPACER.repeat(level * LEVEL_SPACER_AMOUNT);
        var sb = new StringBuilder();
        sb.append(topIntentLevel + section + SECTION_ENDING + System.lineSeparator());

        // TODO: Handle object -> printable nature
        // entries.forEach(entry -> {
        //     if (entry == null) {
        //         return;
        //     }
        //     entry.asPrinter().lines(level + 1).forEach(line -> {
        //         sb.append(line + System.lineSeparator());
        //     });
        // });

        var innerIndentLevel = SPACER.repeat((level + 1)* LEVEL_SPACER_AMOUNT);
        fields.forEach((key, value) -> {
            sb.append(innerIndentLevel + key + SECTION_ENDING + SECTION_SPACER + value + System.lineSeparator());
        });

        messages.forEach((msg) -> {
            sb.append(innerIndentLevel + msg.getLevel() + SECTION_ENDING + SECTION_SPACER + msg.getBody() + System.lineSeparator());
        });

        return sb.toString();
    }

    private List<String> lines(int level) {
        return Arrays.asList(prettyPrint(level).split(System.lineSeparator()));
    }
}
