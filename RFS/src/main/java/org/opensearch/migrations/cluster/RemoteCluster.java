package org.opensearch.migrations.cluster;

import com.rfs.common.OpenSearchClient;

/** Remote cluster */
public interface RemoteCluster extends VersionSpecificCluster {

    /** Remote clusters are communicated with via an OpenSearch client */
    void initialize(OpenSearchClient client);
}
