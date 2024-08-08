package org.opensearch.migrations.cli;

import static org.hamcrest.CoreMatchers.equalTo;
import static org.hamcrest.MatcherAssert.assertThat;

import java.lang.annotation.Target;

import org.junit.jupiter.api.Test;
import org.opensearch.migrations.clusters.Sources;
import org.opensearch.migrations.clusters.RemoteCluster;

import com.rfs.common.ConnectionDetails;

class ClustersTest {
    @Test
    void testPrettyPrint() {
        var clusters = new Clusters();

        clusters.setSource(Sources.withHost("http://source.org"));
        clusters.setTarget(RemoteCluster.builder().url("http://foo.com").build());

        assertThat(clusters.validate(), equalTo(true));

        System.err.println(clusters.asPrinter().prettyPrint(0));
        assertThat(clusters.asPrinter().prettyPrint(0), equalTo("Foo.bar"));
    }

    @Test
    void testPrettyPrint2() {
        var clusters = new Clusters();

        clusters.setSource(Sources.withHost("http://source.org"));

        assertThat(clusters.validate(), equalTo(true));

        System.err.println(clusters.asPrinter().prettyPrint(0));
        assertThat(clusters.asPrinter().prettyPrint(0), equalTo("Foo.bar"));
    }

    @Test
    void testPrettyPrint3() {
        var clusters = new Clusters();

        assertThat(clusters.validate(), equalTo(false));

        System.err.println(clusters.asPrinter().prettyPrint(0));
        assertThat(clusters.asPrinter().prettyPrint(0), equalTo("Foo.bar"));
    }
}
