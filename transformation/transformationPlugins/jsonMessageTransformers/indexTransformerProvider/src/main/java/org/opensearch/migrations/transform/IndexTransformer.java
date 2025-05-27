package org.opensearch.migrations.transform;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import org.opensearch.migrations.transform.typemappings.SourceProperties;

import com.google.common.io.Resources;
import lombok.extern.slf4j.Slf4j;

@Slf4j
public class IndexTransformer extends JavascriptTransformer {

    public static final String INIT_SCRIPT_RESOURCE_NAME = "js/indexTransformer.js";

    public IndexTransformer() throws IOException {
        super(getScripts(), Map.of());
    }

    public static String getScripts() throws IOException {
        return Resources.toString(Resources.getResource(INIT_SCRIPT_RESOURCE_NAME), StandardCharsets.UTF_8);
    }
}
