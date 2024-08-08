package org.opensearch.migrations.clusters;

import com.rfs.models.GlobalMetadata;
import com.rfs.models.IndexMetadata;

public interface SourceCluster {
    Version getVersion();
    GlobalMetadata.Factory getMetadata();
    IndexMetadata.Factory getIndexMetadata();
    
}