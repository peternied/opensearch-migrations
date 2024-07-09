package com.rfs.version_es_6_8;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

import com.rfs.common.SnapshotMetadata;

public class SnapshotMetadataData_ES_6_8 implements SnapshotMetadata.Data {

    private String name;
    private String uuid;
    @JsonProperty("version_id")
    private int versionId;
    private List<String> indices;
    private String state;
    private String reason;
    @JsonProperty("include_global_state")
    private boolean includeGlobalState;
    @JsonProperty("start_time")
    private long startTime;
    @JsonProperty("end_time")
    private long endTime;
    @JsonProperty("total_shards")
    private int totalShards;
    @JsonProperty("successful_shards")
    private int successfulShards;
    private List<?> failures; // Haven't looked at this yet

    @Override
    public String getName() {
        return name;
    }

    @Override
    public String getUuid() {
        return uuid;
    }

    @Override
    public int getVersionId() {
        return versionId;
    }

    @Override
    public List<String> getIndices() {
        return indices;
    }

    @Override
    public String getState() {
        return state;
    }

    @Override
    public String getReason() {
        return reason;
    }

    @Override
    public boolean isIncludeGlobalState() {
        return includeGlobalState;
    }

    @Override
    public long getStartTime() {
        return startTime;
    }

    @Override
    public long getEndTime() {
        return endTime;
    }

    @Override
    public int getTotalShards() {
        return totalShards;
    }

    @Override
    public int getSuccessfulShards() {
        return successfulShards;
    }

    @Override
    public List<?> getFailures() {
        return failures;
    }
}
