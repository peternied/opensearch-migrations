package com.rfs.common;

import org.opensearch.migrations.Version;
import org.opensearch.migrations.VersionMatchers;

import com.rfs.version_es_6_8.SourceResourceProvider_ES_6_8;
import com.rfs.version_es_7_10.SourceResourceProvider_ES_7_10;
import lombok.experimental.UtilityClass;

@UtilityClass
public class SourceResourceProviderFactory {
    public static SourceResourceProvider getProvider(Version version) {
        if (VersionMatchers.isES_6_8.test(version)) {
            return new SourceResourceProvider_ES_6_8();
        }

        if (VersionMatchers.isES_7_X.test(version)) {
                return new SourceResourceProvider_ES_7_10();
        }

        throw new IllegalArgumentException("Invalid version: " + version);
    }

}
