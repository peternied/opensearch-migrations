package org.opensearch.migrations.commands;

import java.nio.file.Path;

import org.opensearch.migrations.Flavor;
import org.opensearch.migrations.Version;
import org.opensearch.migrations.clusters.SourceCluster;

import com.rfs.models.GlobalMetadata;
import com.rfs.models.IndexMetadata;
import com.rfs.common.SnapshotRepo;

import com.rfs.common.FileSystemRepo;
import com.rfs.version_es_7_10.GlobalMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.IndexMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.SnapshotRepoProvider_ES_7_10;


public class LocalSnapshotSource implements SourceCluster {

    private final FileSystemRepo fileSystemRepo;
    private final String snapshotName;
    private final Version version;

    public LocalSnapshotSource(Version version, Path snapshotRepoPath, String snapshotName) {
        this.version = version;
        this.fileSystemRepo = new FileSystemRepo(snapshotRepoPath);
        this.snapshotName = snapshotName;
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
            return new SnapshotRepoProvider_ES_7_10(this.fileSystemRepo);
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
