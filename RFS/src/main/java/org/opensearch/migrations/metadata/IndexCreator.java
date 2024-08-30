package org.opensearch.migrations.metadata;

import java.util.Optional;

import com.fasterxml.jackson.databind.node.ObjectNode;

import com.rfs.models.IndexMetadata;

public interface IndexCreator {
    public Optional<ObjectNode> create(
        IndexMetadata index
    );
}
