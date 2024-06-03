package com.rfs.framework;

import com.rfs.common.IndexMetadata;
import com.rfs.common.OpenSearchClient;

import java.util.List;
import java.nio.file.Path;

public interface SimpleRestoreFromSnapshot {
    public List<IndexMetadata.Data> extraSnapshotIndexData(final String localPath, final String snapshotName, final Path unpackedShardDataDir) throws Exception;
    public void updateTargetCluster(final List<IndexMetadata.Data> indices, final Path unpackedShardDataDir, final OpenSearchClient client) throws Exception;
    @Override
    public default String toString() {
        return this.getClass().getSimpleName();
    }
}
