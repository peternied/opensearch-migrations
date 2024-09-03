package com.rfs.version_os_2_11;

import org.opensearch.migrations.Version;
import org.opensearch.migrations.VersionMatchers;
import org.opensearch.migrations.cluster.ClusterWriter;
import org.opensearch.migrations.cluster.RemoteCluster;
import org.opensearch.migrations.metadata.GlobalMetadataCreator;
import org.opensearch.migrations.metadata.IndexCreator;

import com.rfs.common.OpenSearchClient;
import com.rfs.models.DataFilterArgs;

import lombok.ToString;

@ToString(onlyExplicitlyIncluded = true)
public class RemoteWriter_OS_2_11 implements RemoteCluster, ClusterWriter {
    private Version version;
    @ToString.Include
    private OpenSearchClient client;
    private DataFilterArgs dataFilterArgs;

    @Override
    public boolean compatibleWith(Version version) {
        return VersionMatchers.isOS_2_X.test(version);
    }

    @Override
    public void initialize(DataFilterArgs dataFilterArgs) {
        this.dataFilterArgs = dataFilterArgs;
    }

    @Override
    public void initialize(OpenSearchClient client) {
        this.client = client;
    }

    @Override
    public GlobalMetadataCreator getGlobalMetadataCreator() {
        return new GlobalMetadataCreator_OS_2_11(
            getClient(),
            getDataFilterArgs().indexTemplateAllowlist,
            getDataFilterArgs().componentTemplateAllowlist,
            getDataFilterArgs().indexTemplateAllowlist);
    }

    @Override
    public IndexCreator getIndexCreator() {
        return new IndexCreator_OS_2_11(getClient());
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

    private DataFilterArgs getDataFilterArgs() {
        if (dataFilterArgs == null) {
            throw new UnsupportedOperationException("initialize(...) must be called");
        }
        return dataFilterArgs;
    } 
}
