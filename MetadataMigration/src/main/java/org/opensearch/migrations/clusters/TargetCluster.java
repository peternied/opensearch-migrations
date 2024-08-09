package org.opensearch.migrations.clusters;

import java.util.List;
import org.opensearch.migrations.metadata.tracing.IMetadataMigrationContexts;
import org.opensearch.migrations.metadata.GlobalMetadataCreator;

public interface TargetCluster {
    GlobalMetadataCreator getGlobalMetadataCreator(
        DataFiltersArgs dataFilters,
        IMetadataMigrationContexts.IClusterMetadataContext context);
}
