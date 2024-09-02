package com.rfs.version_remote;

import java.util.ArrayList;
import java.util.List;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.fasterxml.jackson.dataformat.smile.SmileFactory;

import com.rfs.common.OpenSearchClient;
import com.rfs.common.SnapshotRepo.Index;
import com.rfs.common.SnapshotRepo.Provider;
import com.rfs.common.SnapshotRepo.Snapshot;
import com.rfs.common.SourceRepo;
import com.rfs.models.IndexMetadata;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

@RequiredArgsConstructor
@Slf4j
public class RemoteIndexMetadataFactory implements IndexMetadata.Factory {

    private final OpenSearchClient client;

    private ObjectNode indexData;

    private ObjectNode getIndexData() {
        if (indexData == null) {
            indexData = client.getIndexes();
        }
        return indexData;
    }

    @Override
    public IndexMetadata fromRepo(String snapshotName, String indexName) {
        log.info("Ignoring snapshot parameter, getting data from cluster directly");
        return new RemoteIndexMetadata(indexName, (ObjectNode)getIndexData().get(indexName));
    }

    @Override
    public IndexMetadata fromJsonNode(JsonNode root, String indexId, String indexName) {
        throw new UnsupportedOperationException("Unimplemented method 'fromJsonNode'");
    }

    @Override
    public SmileFactory getSmileFactory() {
        throw new UnsupportedOperationException("Unimplemented method 'getSmileFactory'");
    }

    @Override
    public String getIndexFileId(String snapshotName, String indexName) {
        throw new UnsupportedOperationException("Unimplemented method 'getIndexFileId'");
    }

    @Override
    public Provider getRepoDataProvider() {
        return new Provider() {

            @Override
            public List<Snapshot> getSnapshots() {
                throw new UnsupportedOperationException("Unimplemented method 'getSnapshots'");
            }

            @Override
            public List<Index> getIndicesInSnapshot(String snapshotName) {
                var indexes = new ArrayList<Index>();
                getIndexData().fields().forEachRemaining(index -> {
                    indexes.add(new Index() {
                        @Override
                        public String getName() {
                            return index.getKey();
                        }

                        @Override
                        public String getId() {
                            return "<Not sure>";
                        }

                        @Override
                        public List<String> getSnapshots() {
                            return List.of();
                        }
                    });
                });

                return indexes;
            }

            @Override
            public String getSnapshotId(String snapshotName) {
                throw new UnsupportedOperationException("Unimplemented method 'getSnapshotId'");
            }

            @Override
            public String getIndexId(String indexName) {
                throw new UnsupportedOperationException("Unimplemented method 'getIndexId'");
            }

            @Override
            public SourceRepo getRepo() {
                throw new UnsupportedOperationException("Unimplemented method 'getRepo'");
            }
        };
    }
    
}
