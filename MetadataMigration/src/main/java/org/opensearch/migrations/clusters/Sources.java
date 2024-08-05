package org.opensearch.migrations.clusters;

public class Sources {
    public static SourceCluster withHost(String url) {
        return new HostSource.HostSourceBuilder()
            .url(url)
            .flavor("Elasticsearch")
            .version(680)
            .build();
    }
}
