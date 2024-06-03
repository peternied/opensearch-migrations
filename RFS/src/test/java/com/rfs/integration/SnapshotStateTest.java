package com.rfs.integration;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtensionContext;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.ArgumentsProvider;
import org.junit.jupiter.params.provider.ArgumentsSource;
import org.mockito.ArgumentCaptor;

import com.rfs.common.OpenSearchClient;
import com.rfs.framework.ClusterOperations;
import com.rfs.framework.ElasticsearchContainer;
import com.rfs.framework.SimpleRestoreFromSnapshot;
import com.rfs.framework.SimpleRestoreFromSnapshot_ES_6_8;
import com.rfs.framework.SimpleRestoreFromSnapshot_ES_7_10;
import com.rfs.framework.ElasticsearchContainer.Version;

import lombok.Builder;
import lombok.Data;
import reactor.core.publisher.Mono;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoMoreInteractions;
import static org.mockito.Mockito.when;
import static org.hamcrest.CoreMatchers.allOf;
import static org.hamcrest.CoreMatchers.anyOf;
import static org.hamcrest.CoreMatchers.containsString;
import static org.hamcrest.CoreMatchers.not;
import static org.hamcrest.MatcherAssert.assertThat;

import java.io.File;
import java.util.List;
import java.nio.file.Path;
import java.util.stream.Stream;
import java.util.function.Supplier;

/**
 * Tests focused on setting up different snapshot states and then verifying the behavior of RFS towards the target cluster
 */
public class SnapshotStateTest {

    @TempDir
    private File localDirectory;
    private List<AutoCloseable> closables;

    public ClusterOperations setUp(final ElasticsearchContainer.Version version) throws Exception {
        final var cluster = new ElasticsearchContainer(version);
        cluster.start();
        this.closables = List.of(cluster);

        final var operations = new ClusterOperations(cluster.getUrl());
        operations.createSnapshotRepository();

        return operations;
    }

    @AfterEach
    public void tearDown() throws Exception {
        for (final var closable : closables) {
            closable.close();
        }
        closables = null;
    }

    private static class SnapshotTestMatrix implements ArgumentsProvider {

        @Override
        public Stream<? extends Arguments> provideArguments(ExtensionContext context) throws Exception {
            return Stream.of(
                Arguments.of(
                    Version.V7_10_2,
                    new SimpleRestoreFromSnapshot_ES_7_10()),
                Arguments.of(
                    Version.V6_8_23,
                    new SimpleRestoreFromSnapshot_ES_6_8())
                );
        }
    }

    @ParameterizedTest
    @ArgumentsSource(SnapshotTestMatrix.class)
    public void SingleSnapshot_SingleDocument(final ElasticsearchContainer.Version cluster, final SimpleRestoreFromSnapshot srfs) throws Exception {
        // Setup
        final var operations = setUp(cluster);
        final var indexName = "my-index";
        final var document1Id = "doc1";
        final var document1Body = "{\"fo$o\":\"bar\"}";
        operations.createDocument(indexName, document1Id, document1Body);

        final var snapshotName = "snapshot-1";
        operations.takeSnapshot(snapshotName, indexName);

        final File snapshotCopy = new File(localDirectory + "/snapshotCopy");
        cluster.copySnapshotData(snapshotCopy.getAbsolutePath());

        final var unpackedShardDataDir = Path.of(localDirectory.getAbsolutePath() + "/unpacked-shard-data");
        final var indices = srfs.extraSnapshotIndexData(snapshotCopy.getAbsolutePath(), snapshotName, unpackedShardDataDir);

        final var client = mock(OpenSearchClient.class);
        when(client.sendBulkRequest(any(), any())).thenReturn(Mono.empty());

        // Action
        srfs.updateTargetCluster(indices, unpackedShardDataDir, client);

        // Validation
        final var bodyCaptor = ArgumentCaptor.forClass(String.class);
        verify(client, times(1)).sendBulkRequest(eq(indexName), bodyCaptor.capture());
        final var bulkRequestRaw = bodyCaptor.getValue();
        assertThat(bulkRequestRaw, allOf(containsString(document1Id), containsString(document1Body)));

        verifyNoMoreInteractions(client);
    }

    // @Test
    // @Disabled("https://opensearch.atlassian.net/browse/MIGRATIONS-1746")
    // public void SingleSnapshot_SingleDocument_Then_DeletedDocument() throws Exception {
    //     // Setup
    //     final var indexName = "my-index-with-deleted-item";
    //     final var document1Id = "doc1-going-to-be-deleted";
    //     final var document1Body = "{\"foo\":\"bar\"}";
    //     operations.createDocument(indexName, document1Id, document1Body);
    //     operations.deleteDocument(indexName, document1Id);
    //     final var snapshotName = "snapshot-delete-item";
    //     operations.takeSnapshot(snapshotName, indexName);

    //     final File snapshotCopy = new File(localDirectory + "/snapshotCopy");
    //     cluster.copySnapshotData(snapshotCopy.getAbsolutePath());

    //     final var unpackedShardDataDir = Path.of(localDirectory.getAbsolutePath() + "/unpacked-shard-data");
    //     final var indices = srfs.extraSnapshotIndexData(snapshotCopy.getAbsolutePath(), snapshotName, unpackedShardDataDir);

    //     final var client = mock(OpenSearchClient.class);
    //     when(client.sendBulkRequest(any(), any())).thenReturn(Mono.empty());

    //     // Action
    //     srfs.updateTargetCluster(indices, unpackedShardDataDir, client);

    //     // Validation
    //     final var bodyCaptor = ArgumentCaptor.forClass(String.class);
    //     verify(client, times(1)).sendBulkRequest(eq(indexName), bodyCaptor.capture());
    //     final var bulkRequestRaw = bodyCaptor.getValue();
    //     assertThat(bulkRequestRaw, not(anyOf(containsString(document1Id), containsString(document1Body))));

    //     verifyNoMoreInteractions(client);
    // }

    // @Test
    // @Disabled("https://opensearch.atlassian.net/browse/MIGRATIONS-1747")
    // public void SingleSnapshot_SingleDocument_Then_UpdateDocument() throws Exception {
    //     // Setup
    //     final var indexName = "my-index-with-updated-item";
    //     final var document1Id = "doc1-going-to-be-updated";
    //     final var document1BodyOrginal = "{\"foo\":\"bar\"}";
    //     operations.createDocument(indexName, document1Id, document1BodyOrginal);
    //     final var document1BodyUpdated = "{\"actor\":\"troy mcclure\"}";
    //     operations.createDocument(indexName, document1Id, document1BodyUpdated);

    //     final var snapshotName = "snapshot-delete-item";
    //     operations.takeSnapshot(snapshotName, indexName);

    //     final File snapshotCopy = new File(localDirectory + "/snapshotCopy");
    //     cluster.copySnapshotData(snapshotCopy.getAbsolutePath());

    //     final var unpackedShardDataDir = Path.of(localDirectory.getAbsolutePath() + "/unpacked-shard-data");
    //     final var indices = srfs.extraSnapshotIndexData(snapshotCopy.getAbsolutePath(), snapshotName, unpackedShardDataDir);

    //     final var client = mock(OpenSearchClient.class);
    //     when(client.sendBulkRequest(any(), any())).thenReturn(Mono.empty());

    //     // Action
    //     srfs.updateTargetCluster(indices, unpackedShardDataDir, client);

    //     // Validation
    //     final var bodyCaptor = ArgumentCaptor.forClass(String.class);
    //     verify(client, times(1)).sendBulkRequest(eq(indexName), bodyCaptor.capture());
    //     final var bulkRequestRaw = bodyCaptor.getValue();
    //     assertThat(bulkRequestRaw, allOf(containsString(document1Id), containsString(document1BodyUpdated), not(containsString(document1BodyOrginal))));

    //     verifyNoMoreInteractions(client);
    // }
}
