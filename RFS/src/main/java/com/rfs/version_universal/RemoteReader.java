package com.rfs.version_universal;

import org.opensearch.migrations.Version;
import org.opensearch.migrations.VersionMatchers;
import org.opensearch.migrations.cluster.ClusterReader;
import org.opensearch.migrations.cluster.RemoteCluster;

import com.rfs.common.OpenSearchClient;
import com.rfs.models.GlobalMetadata.Factory;

import lombok.ToString;

@ToString(onlyExplicitlyIncluded = true)
public class RemoteReader implements RemoteCluster, ClusterReader {
    private Version version;
    @ToString.Include
    private OpenSearchClient client;

    @Override
    public boolean compatibleWith(Version version) {
        return VersionMatchers.isES_7_X
            .or(VersionMatchers.isOS_1_X)
            .or(VersionMatchers.isOS_2_X)
            .test(version);
    }

    @Override
    public void initialize(OpenSearchClient client) {
        this.client = client;
    }

    @Override
    public Factory getGlobalMetadata() {
        return new RemoteMetadataFactory(getClient());
    }

    @Override
    public com.rfs.models.IndexMetadata.Factory getIndexMetadata() {
        return new RemoteIndexMetadataFactory(getClient());
    }

    @ToString.Include
    @Override
    public Version getVersion() {
        if (version == null) {
            version = getClient().getClusterVersion();
        }
        return version;
    }

    private OpenSearchClient getClient() {
        if (client == null) {
            throw new UnsupportedOperationException("initialize(...) must be called");
        }
        return client;
    }
}
