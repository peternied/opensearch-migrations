package org.opensearch.migrations.clusters;

import org.opensearch.migrations.metadata.tracing.IMetadataMigrationContexts;
import org.opensearch.migrations.DataFiltersArgs;
import org.opensearch.migrations.metadata.GlobalMetadataCreator;
import org.opensearch.migrations.metadata.IndexCreator;

public interface TargetCluster {
    public GlobalMetadataCreator getGlobalMetadataCreator(
        DataFiltersArgs dataFilters,
        IMetadataMigrationContexts.IClusterMetadataContext context);

    public IndexCreator getIndexCreator();
}
