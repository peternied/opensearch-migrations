package com.rfs.framework;

import java.nio.file.Path;
import java.util.List;
import java.util.stream.Collectors;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.lucene.util.IOUtils;

import com.rfs.common.DefaultSourceRepoAccessor;
import com.rfs.common.DocumentReindexer;
import com.rfs.common.FileSystemRepo;
import com.rfs.common.IndexMetadata;
import com.rfs.common.LuceneDocumentsReader;
import com.rfs.common.OpenSearchClient;
import com.rfs.common.SnapshotRepo;
import com.rfs.common.SnapshotShardUnpacker;
import com.rfs.version_es_7_10.IndexMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.ShardMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.SnapshotRepoProvider_ES_7_10;

/**
 * Simplified version of RFS for use in testing - ES 7.10 version.
 */
public class SimpleRestoreFromSnapshot_ES_7_10 implements SimpleRestoreFromSnapshot {

    private static final Logger logger = LogManager.getLogger(SimpleRestoreFromSnapshot_ES_7_10.class);

    public List<IndexMetadata.Data> extractSnapshotIndexData(
        final String localPath,
        final String snapshotName,
        final Path unpackedShardDataDir
    ) throws Exception {
        IOUtils.rm(unpackedShardDataDir);

        final var repo = new FileSystemRepo(Path.of(localPath));
        SnapshotRepo.Provider snapShotProvider = new SnapshotRepoProvider_ES_7_10(repo);
        final List<IndexMetadata.Data> indices = snapShotProvider.getIndicesInSnapshot(snapshotName)
            .stream()
            .map(index -> {
                try {
                    return new IndexMetadataFactory_ES_7_10(snapShotProvider).fromRepo(snapshotName, index.getName());
                } catch (final Exception e) {
                    throw new RuntimeException(e);
                }
            })
            .collect(Collectors.toList());

        for (final IndexMetadata.Data index : indices) {
            for (int shardId = 0; shardId < index.getNumberOfShards(); shardId++) {
                var shardMetadata = new ShardMetadataFactory_ES_7_10(snapShotProvider).fromRepo(
                    snapshotName,
                    index.getName(),
                    shardId
                );
                DefaultSourceRepoAccessor repoAccessor = new DefaultSourceRepoAccessor(repo);
                SnapshotShardUnpacker unpacker = new SnapshotShardUnpacker(
                    repoAccessor,
                    unpackedShardDataDir,
                    shardMetadata,
                    Integer.MAX_VALUE
                );
                unpacker.unpack();
            }
        }
        return indices;
    }

    public void updateTargetCluster(
        final List<IndexMetadata.Data> indices,
        final Path unpackedShardDataDir,
        final OpenSearchClient client
    ) throws Exception {
        for (final IndexMetadata.Data index : indices) {
            for (int shardId = 0; shardId < index.getNumberOfShards(); shardId++) {
                final var documents = new LuceneDocumentsReader(
                    unpackedShardDataDir.resolve(index.getName()).resolve("" + shardId)
                ).readDocuments();

                final var finalShardId = shardId;
                new DocumentReindexer(client).reindex(index.getName(), documents)
                    .doOnError(error -> logger.error("Error during reindexing: " + error))
                    .doOnSuccess(
                        done -> logger.info(
                            "Reindexing completed for index " + index.getName() + ", shard " + finalShardId
                        )
                    )
                    .block();
            }
        }
    }
}
