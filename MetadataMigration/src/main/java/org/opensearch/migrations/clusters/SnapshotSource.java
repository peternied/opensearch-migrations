package org.opensearch.migrations.clusters;

import java.nio.file.Path;

import org.opensearch.migrations.Flavor;
import org.opensearch.migrations.Version;

import com.rfs.models.GlobalMetadata;
import com.rfs.models.IndexMetadata;
import com.rfs.common.SnapshotRepo;
import com.rfs.common.S3Repo;
import com.rfs.common.SourceRepo;

import com.rfs.common.FileSystemRepo;
import com.rfs.version_es_7_10.GlobalMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.IndexMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.SnapshotRepoProvider_ES_7_10;

import com.rfs.common.S3Uri;


public class SnapshotSource implements SourceCluster {

    private final SourceRepo repo;
    private final Version version;

    public SnapshotSource(Version version, String snapshotRepoPath) {
        this.version = version;
        this.repo = new FileSystemRepo(Path.of(snapshotRepoPath));
    }

    public SnapshotSource(Version version, String s3LocalDirPath, String s3RepoUri, String s3Region) {
        this.version = version;
        this.repo = S3Repo.create(Path.of(s3LocalDirPath), new S3Uri(s3RepoUri), s3Region);
    }

    @Override
    public Version getVersion() {
        // Make sure the snapshot exists
        //   Else throw
        // Read the snapshot file, get the version
        //   Else throw
        //
        return version;
    }

    private SnapshotRepo.Provider getProvider() {
        if (version.equals(Version.builder().flavor(Flavor.Elasticsearch).major(7).minor(10).build())) {
            return new SnapshotRepoProvider_ES_7_10(this.repo);
        }

        throw new UnsupportedOperationException("Unsupported version " + getVersion());
    }

    @Override
    public GlobalMetadata.Factory getMetadata() {
        if (version.equals(Version.builder().flavor(Flavor.Elasticsearch).major(7).minor(10).build())) {
            return new GlobalMetadataFactory_ES_7_10(getProvider());
        }

        throw new UnsupportedOperationException("Unsupported version " + getVersion());
    }

    @Override
    public IndexMetadata.Factory getIndexMetadata() {
        if (version.equals(Version.builder().flavor(Flavor.Elasticsearch).major(7).minor(10).build())) {
            return new IndexMetadataFactory_ES_7_10(getProvider());
        }

        throw new UnsupportedOperationException("Unsupported version " + getVersion());
    }

}
