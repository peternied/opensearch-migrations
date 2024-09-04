package com.rfs.version_universal;

import org.opensearch.migrations.Version;
import org.opensearch.migrations.VersionMatchers;
import org.opensearch.migrations.cluster.ClusterReader;
import org.opensearch.migrations.cluster.RemoteCluster;

import com.rfs.common.http.ConnectionContext;
import com.rfs.models.GlobalMetadata.Factory;

public class RemoteReader implements RemoteCluster, ClusterReader {
    private Version version;
    private RemoteReaderClient client;
    private ConnectionContext connection;

    @Override
    public boolean compatibleWith(Version version) {
        return VersionMatchers.isES_7_X
            .or(VersionMatchers.isOS_1_X)
            .or(VersionMatchers.isOS_2_X)
            .test(version);
    }

    @Override
    public void initialize(ConnectionContext connection) {
        this.connection = connection;
    }

    @Override
    public Factory getGlobalMetadata() {
        return new RemoteMetadataFactory(getClient());
    }

    @Override
    public com.rfs.models.IndexMetadata.Factory getIndexMetadata() {
        return new RemoteIndexMetadataFactory(getClient());
    }

    @Override
    public Version getVersion() {
        if (version == null) {
            version = getClient().getClusterVersion();
        }
        return version;
    }

    public String toString() {
        // These values could be null, don't want to crash during toString
        return String.format("Remote Cluster: %s %s", version, connection);
    }

    private RemoteReaderClient getClient() {
        if (client == null) {
            client = new RemoteReaderClient(getConnection());
        }
        return client;
    }

    private ConnectionContext getConnection() {
        if (connection == null) {
            throw new UnsupportedOperationException("initialize(...) must be called");
        }
        return connection;
    }
}
