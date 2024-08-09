package org.opensearch.migrations.metadata;

import com.rfs.models.GlobalMetadata;

public interface GlobalMetadataCreator {
    public void create(GlobalMetadata metadata);
}
