package com.rfs.version_remote;

import com.fasterxml.jackson.databind.node.ObjectNode;

import com.rfs.models.GlobalMetadata;
import lombok.AllArgsConstructor;

@AllArgsConstructor
public class RemoteMetadata implements GlobalMetadata {

    private ObjectNode sourceData;

    @Override
    public ObjectNode toObjectNode() {
        return sourceData;
    }
}
