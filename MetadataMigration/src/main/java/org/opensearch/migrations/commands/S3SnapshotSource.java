package org.opensearch.migrations.commands;

import java.nio.file.Path;

import org.opensearch.migrations.Version;
import org.opensearch.migrations.clusters.SourceCluster;

import com.rfs.models.GlobalMetadata;
import com.rfs.models.IndexMetadata;

public class S3SnapshotSource implements SourceCluster {

    public S3SnapshotSource(Path s3LocalDirPath, String s3RepoUri, String s3Region) {
        //TODO Auto-generated constructor stub
    }

    @Override
    public Version getVersion() {
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
