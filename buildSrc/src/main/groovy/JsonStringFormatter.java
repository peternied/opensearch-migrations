import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class JsonStringFormatter {
    private static final ObjectMapper objectMapper = new ObjectMapper();

    // Pattern to match multi-line string literals in Java
    private static final Pattern MULTILINE_STRING_PATTERN = Pattern.compile(
        "\"[^\"]*\"\\s*\\+\\s*\"[^\"]*\"");

    static {
        objectMapper.enable(SerializationFeature.INDENT_OUTPUT);
    }

    public static String format(String input) {
        Matcher matcher = MULTILINE_STRING_PATTERN.matcher(input);
        StringBuffer formattedString = new StringBuffer();

        while (matcher.find()) {
            String multilineString = matcher.group();
            System.out.println("STRING " + multilineString);
            // Remove concatenation operators and extra quotes for processing
            String concatenatedString = multilineString.replaceAll("\\\"\\s*\\+\\s*\\\"", "").replaceAll("^\"|\"$", "");

            if (isValidJson(concatenatedString)) {
                try {
                    Object json = objectMapper.readValue(concatenatedString, Object.class);
                    String formattedJson = objectMapper.writerWithDefaultPrettyPrinter().writeValueAsString(json);
                    // Rebuild the Java string with properly formatted JSON
                    String javaFormattedJson = "\"" + formattedJson.replace("\n", "\\n\" +\n\"").replaceAll(" +", " ") + "\"";
                    matcher.appendReplacement(formattedString, Matcher.quoteReplacement(javaFormattedJson));
                } catch (Exception e) {
                    // If there's an error, return the original string
                    matcher.appendReplacement(formattedString, multilineString);
                }
            } else {
                matcher.appendReplacement(formattedString, multilineString);
            }
        }
        matcher.appendTail(formattedString);
        return formattedString.toString();
    }

    private static boolean isValidJson(String jsonString) {
        try {
            objectMapper.readTree(jsonString);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
