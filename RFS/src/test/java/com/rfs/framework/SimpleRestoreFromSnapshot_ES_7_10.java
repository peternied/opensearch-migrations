package com.rfs.framework;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyInt;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.withSettings;

import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.lucene.util.IOUtils;
import org.mockito.Mockito;

import com.rfs.cms.CmsClient;
import com.rfs.cms.CmsEntry;
import com.rfs.cms.CmsEntry.DocumentsStatus;
import com.rfs.cms.CmsEntry.Documents;
import com.rfs.common.DocumentReindexer;
import com.rfs.common.FileSystemRepo;
import com.rfs.common.IndexMetadata;
import com.rfs.common.LuceneDocumentsReader;
import com.rfs.common.OpenSearchClient;
import com.rfs.common.ShardMetadata;
import com.rfs.common.SnapshotRepo;
import com.rfs.common.SnapshotShardUnpacker;
import com.rfs.version_es_7_10.IndexMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.ShardMetadataFactory_ES_7_10;
import com.rfs.version_es_7_10.SnapshotRepoProvider_ES_7_10;
import com.rfs.worker.DocumentsRunner;
import com.rfs.worker.GlobalState;

/**
 * Simplified version of RFS for use in testing - ES 7.10 version.
 */
public class SimpleRestoreFromSnapshot_ES_7_10 implements SimpleRestoreFromSnapshot {

    private static final Logger logger = LogManager.getLogger(SimpleRestoreFromSnapshot_ES_7_10.class);

    public List<IndexMetadata.Data> extractSnapshotIndexData(final String localPath, final String snapshotName, final Path unpackedShardDataDir) throws Exception {
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
                var shardMetadata = new ShardMetadataFactory_ES_7_10(snapShotProvider).fromRepo(snapshotName, index.getName(), shardId);
                SnapshotShardUnpacker unpacker = new SnapshotShardUnpacker(repo, unpackedShardDataDir, Integer.MAX_VALUE);
                unpacker.unpack(shardMetadata);
            }
        }
        return indices;
    }

    public void updateTargetCluster(final List<IndexMetadata.Data> indices, final Path unpackedShardDataDir, final OpenSearchClient client) throws Exception {
        for (final IndexMetadata.Data index : indices) {
            for (int shardId = 0; shardId < index.getNumberOfShards(); shardId++) {
                final var documents = new LuceneDocumentsReader(unpackedShardDataDir).readDocuments(index.getName(), shardId);

                final var finalShardId = shardId;
                new DocumentReindexer(client).reindex(index.getName(), documents)
                    .doOnError(error -> logger.error("Error during reindexing: " + error))
                    .doOnSuccess(done -> logger.info("Reindexing completed for index " + index.getName() + ", shard " + finalShardId))
                    .block();
            }
        }
    }

    public void copyDocs(final String localPath, final String snapshotName, final Path unpackedShardDataDir, final OpenSearchClient client){
        final var repo = new FileSystemRepo(Path.of(localPath));

        SnapshotRepo.Provider snapShotProvider = new SnapshotRepoProvider_ES_7_10(repo);

        ShardMetadata.Factory shardMetadataFactory = new ShardMetadataFactory_ES_7_10(snapShotProvider);
        SnapshotShardUnpacker unpacker = new SnapshotShardUnpacker(repo, unpackedShardDataDir, Integer.MAX_VALUE);
        LuceneDocumentsReader reader = new LuceneDocumentsReader(unpackedShardDataDir);
        DocumentReindexer reindexer = new DocumentReindexer(client);

        final var globalState = Mockito.mock(GlobalState.class);
        final var cmsClient = Mockito.mock(CmsClient.class, withSettings()
            .defaultAnswer((inv) -> { throw new RuntimeException("a" + inv); }));

        final var docs = new Documents(DocumentsStatus.SETUP, CmsEntry.Documents.getLeaseExpiry(0, 1), 1);

        final var docsRef = new AtomicReference<Documents>(docs);
        // Handle DocumentsEntry
        doAnswer(inv -> {
            return Optional.of(docsRef.get());
        }).when(cmsClient).createDocumentsEntry();

        doAnswer(inv -> {
            return Optional.of(docsRef.get());
        }).when(cmsClient).getDocumentsEntry();

        doAnswer(inv -> {
            final Documents updated = inv.getArgument(0);
            docsRef.set(updated);
            return Optional.of(docsRef.get());
        }).when(cmsClient).updateDocumentsEntry(any(), any());

        // Handle DocumentsWorkItems
        doAnswer(inv -> {
            final Documents updated = inv.getArgument(0);
            docsRef.set(updated);
            return Optional.of(docsRef.get());
        }).when(cmsClient).createDocumentsWorkItem(any(), anyInt());
        // TODO: need to return all the index and shard ids called by createDocumentsWorkItem
        doReturn(Optional.empty()).when(cmsClient).getAvailableDocumentsWorkItem();

        final var indexMetadataFactory = new IndexMetadataFactory_ES_7_10(snapShotProvider);

        DocumentsRunner documentsWorker = new DocumentsRunner(globalState, cmsClient, snapshotName, indexMetadataFactory, shardMetadataFactory, unpacker, reader, reindexer);
        documentsWorker.run();
    }
}
