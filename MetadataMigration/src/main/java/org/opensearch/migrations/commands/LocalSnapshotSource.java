package org.opensearch.migrations.commands;

import java.nio.file.Path;

import org.opensearch.migrations.Version;
import org.opensearch.migrations.clusters.SourceCluster;

import com.rfs.models.GlobalMetadata;
import com.rfs.models.IndexMetadata;

import com.rfs.common.FileSystemRepo;

public class LocalSnapshotSource implements SourceCluster {

    private final FileSystemRepo fileSystemRepo;
    private final String snapshotName;

    public LocalSnapshotSource(Path snapshotRepoPath, String snapshotName) {
        this.snapshotName = snapshotName;
        this.fileSystemRepo = new FileSystemRepo(snapshotRepoPath);
    }

    @Override
    public Version getVersion() {
        // Make sure the snapshot exists
        //   Else throw
        // Read the snapshot file, get the version
        //   Else throw
        //

        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getVersion'");
    }

    @Override
    public GlobalMetadata.Factory getMetadata() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getMetadata'");
    }

    @Override
    public IndexMetadata.Factory getIndexMetadata() {
        // TODO Auto-generated method stub
        throw new UnsupportedOperationException("Unimplemented method 'getIndexMetadata'");
    }

}
