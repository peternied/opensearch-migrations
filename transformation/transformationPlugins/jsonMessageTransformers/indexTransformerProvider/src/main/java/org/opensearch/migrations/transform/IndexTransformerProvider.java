package org.opensearch.migrations.transform;

import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.opensearch.migrations.transform.typemappings.SourceProperties;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class IndexTransformerProvider extends JsonJSTransformerProvider {

    private static final ObjectMapper MAPPER = new ObjectMapper();

    @SneakyThrows
    @Override
    @SuppressWarnings("unchecked")
    public IJsonTransformer createTransformer(Object jsonConfig) {
        try {
            log.debug("IndexTransformerProvider with config: {}", jsonConfig);
            var config = MAPPER.readTree() validateAndExtractConfig(jsonConfig, new String[]{});
            log.debug("Validated config: {}", config);

            return new IndexTransformer();
        } catch (ClassCastException e) {
            log.error("Configuration error: {}", e.getMessage(), e);
            throw new IllegalArgumentException(getConfigUsageStr(), e);
        }
    }

    @Override
    protected String getConfigUsageStr() {
        // TODO: Write usage.
        return this.getClass().getName() + "'s usage details to be determined...";
    }
}
