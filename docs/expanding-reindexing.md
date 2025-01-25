# Expanding Reindexing

Reindexing from Snapshot (RFS) was built for the Migration Assistant and has been adoption because it is low risk to the source cluster.  Snapshots house the data that is an Elasticsearch / OpenSearch cluster in a place that is outside of the cluster.  In the case of the Amazon Managed OpenSearch these snapshots are stored in S3, an ideal place to read from - decoupling the source cluster bottle-necking the target cluster.  Full background for the see the current [RFS Design](../RFS/docs/DESIGN.md).

```mermaid
sequenceDiagram
    title RFS Process
    participant sc as Source Cluster
    participant s3 as Snapshot Store (S3)
    participant rfs1 as RFS Worker
    participant tc as Target Cluster

    sc ->> s3: Create snapshot
    note over rfs1: Workers can vertical scale
    rfs1 ->> tc: Acquire work lease
    rfs1 ->> s3: Download snapshot
    rfs1 ->> tc: Reindex data
```

- [Expanding Reindexing](#expanding-reindexing)
  - [Limitations](#limitations)
    - [Worker Coordination](#worker-coordination)
    - [Upfront download and working space](#upfront-download-and-working-space)
    - [Horizontal scale limits](#horizontal-scale-limits)
    - [Lucene Support over time](#lucene-support-over-time)
  - [Proposals (High Level)](#proposals-high-level)
    - [Deploy PostgreSQL database for work coordination](#deploy-postgresql-database-for-work-coordination)
    - [Decouple Reindexing from the Snapshot](#decouple-reindexing-from-the-snapshot)

## Limitations

RFS has limits on governed by its current structure:
- Work leases are managed on target cluster
- Large upfront download and working space volume
- Common issue oversized shard also limits RFS horizontal scaling
- Loading older lucene formats


### Worker Coordination

RFS is meant to run in a distributed way with many workers coming up at once and no external data stores.  Using the target cluster for state management was the cleanest approach available using a worker lease based  system.

Unfortunately, OpenSearch does **not** support strict definitions of Atomicity, Consistency, Isolation, or Durability - the standards of [ACID Compliant databases](https://www.mongodb.com/resources/products/capabilities/acid-compliance).  While there is an implementation of a worker lease management system, its complex and as we expand supported target versions it might break in unexpected ways.

Additional since the target cluster is where the documents are being reindexed keeping the worker lease traffic low is a requirement because with too many RFS workers writing to the store at once could cause contention and failures processing traffic.

### Upfront download and working space

The snapshot is not directly usable from S3, it needs to be pre-processed by downloading and read into Lucene (the underlying technology use for document storage / indexing).  This process requires non-sequential reads that make streaming from s3 complex, requiring a caching layer that might effectively need to cache the whole shard.

The size of the working space is governed by the shard size, with customers having shards that are more than 500GB in size, this requires that working space to be sized at least as big as the cluster.

Together this means that after RFS has started there could be considerable time before data is reindex, and if there are issues that cause a RFS worker to be restarted considerable download and processing time could be repeated.

```mermaid
gantt
    title RFS Worker Process Timeline
    dateFormat  HH:mm
    axisFormat  %H:%M
    section Tasks
    Download Snapshot  :active, d1, 00:00   , 24m
    Unpack Snapshot    :active, d2, after d1, 6m
    Reindex to Target  :active, d3, after d2, 30m
```

### Horizontal scale limits

Over the lifetime of an OpenSearch cluster customers tend to discover that the sharding strategy choice made when an index is first created needs to be tweaked.  A common example is that index has 2 shards, in a cluster with 4 data nodes, only a half of the nodes can handle index or query requests - a large amount of unused compute.

During a migration the target cluster could set the sharding size to 4 and use all nodes in the cluster.  However, RFS only can divide its workload by shards which are the units that are downloaded and unpacked, maxing out the number of concurrent workers at 2.

**Reshard with 1 to 2 Expansion**
```mermaid
graph TD
    subgraph Snapshot
        scNode1[Shard1]
        scNode2[Shard2]
    end

    scNode1 --> shard1
    scNode2 --> shard2

    subgraph RFSWorker1
        shard1[Processing: Shard1]
    end

    subgraph RFSWorker2
        shard2[Processing: Shard2]
    end

    subgraph TargetCluster
        Node1
        Node2
        Node3
        Node4
    end

    shard1 -->|50% load + 2x overhead| Node1
    shard1 -->|50% load + 2x overhead| Node2
    shard2 -->|50% load + 2x overhead| Node3
    shard2 -->|50% load + 2x overhead| Node4
```

Work in flight for subshard processing allows dividing shard data into chunks by it's sequence number.  These chunks would contain documents `chunk1:[1..n]` and  `chunk2:[n+1..]`. The striping process is the hashcode of the document id, so the hash space of chunk1 and chunk2 are effectively the same.

In practice this means if you had a single shard that is to be migrated into 4 shards on the target, only use a single RFS worker with its' load is spread equally. Since the work is fanning out farther, its causing even more overhead on the cluster.

While using subshard to chunk into 4 pieces could scale up the number of RFS workers, but paying the additional overhead tax.    

**Reshard with 1 to 4 Expansion**
```mermaid
graph TD
    subgraph Snapshot
        scNode1[Shard1]
    end

    scNode1 --> shard1

    subgraph RFSWorker1
        shard1[Processing: Shard1]
    end

    subgraph TargetCluster
        Node1
        Node2
        Node3
        Node4
    end

    shard1 -->|25% load + 4x overhead| Node1
    shard1 -->|25% load + 4x overhead| Node2
    shard1 -->|25% load + 4x overhead| Node3
    shard1 -->|25% load + 4x overhead| Node4
```

### Lucene Support over time

OpenSearch is a distributed system wrapper over Lucene a text search and indexing system.  Those snapshots are like-wise a thin wrapper of the serialized lucene indexes and document data.

Those unpacking processes are done so that RFS can use lucene to directly read the snapshot data to extract the documents in that data to be collected and reindexed against the target cluster.

Lucene has a backwards compatibility story where it supports reading a subset of the previous versions of lucene via [backwards-codecs](https://stackoverflow.com/a/53390082/533057).  We are currently using lucene v9 and have success reading lucene data created in Elasticsearch 6.8 using lucene v7.  However, for customers that upgraded from Elasticsearch 5.6 -> Elasticsearch 6.8 they might have lucene data that was created in lucene v6 - which we cannot read.

**OpenSearch Lucene Mapping**
```mermaid
flowchart TD
    subgraph OpenSearch
    OpenSearch_2x("OpenSearch 2.x")
    OpenSearch_1x("OpenSearch 1.3")
    end 
    subgraph Lucene
    Lucene_9x("Lucene 9.x")
    Lucene_8x("Lucene 8.x")
    Lucene_7x("Lucene 7.x")
    Lucene_6x("Lucene 6.x")
    Lucene_5x("Lucene 5.x")
    end

    OpenSearch_2x ==> Lucene_9x
    OpenSearch_2x --> Lucene_8x
    OpenSearch_1x ==> Lucene_8x
    OpenSearch_1x --> Lucene_7x

    style Lucene_9x fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style Lucene_8x fill:#FFC107,stroke:#FFA000,stroke-width:2px
    style Lucene_7x fill:#2196F3,stroke:#1976D2,stroke-width:2px
    style Lucene_6x fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px
    style Lucene_5x fill:#F44336,stroke:#D32F2F,stroke-width:2px

    style OpenSearch_2x fill:#A5C956,stroke:#7BA03A,stroke-width:2px
    style OpenSearch_1x fill:#D1A634,stroke:#A37700,stroke-width:2px
```

**Elasticsearch Lucene Mapping**
```mermaid
flowchart TD
    subgraph Elastic
    Elasticsearch_8x("Elasticsearch 8.x")
    Elasticsearch_710("Elasticsearch 7.10")
    Elasticsearch_68("Elasticsearch 6.8")
    Elasticsearch_56("Elasticsearch 5.6")
    end
    subgraph Lucene
    Lucene_9x("Lucene 9.x")
    Lucene_8x("Lucene 8.x")
    Lucene_7x("Lucene 7.x")
    Lucene_6x("Lucene 6.x")
    Lucene_5x("Lucene 5.x")
    end

    Elasticsearch_8x ==> Lucene_9x
    Elasticsearch_8x --> Lucene_8x
    Elasticsearch_710 ==> Lucene_8x
    Elasticsearch_710 --> Lucene_7x
    Elasticsearch_68 ==> Lucene_7x
    Elasticsearch_68 --> Lucene_6x
    Elasticsearch_56 ==> Lucene_6x
    Elasticsearch_56 --> Lucene_5x

    style Lucene_9x fill:#4CAF50,stroke:#2E7D32,stroke-width:2px
    style Lucene_8x fill:#FFC107,stroke:#FFA000,stroke-width:2px
    style Lucene_7x fill:#2196F3,stroke:#1976D2,stroke-width:2px
    style Lucene_6x fill:#9C27B0,stroke:#7B1FA2,stroke-width:2px
    style Lucene_5x fill:#F44336,stroke:#D32F2F,stroke-width:2px

    style Elasticsearch_8x fill:#A5C956,stroke:#7BA03A,stroke-width:2px
    style Elasticsearch_710 fill:#D1A634,stroke:#A37700,stroke-width:2px
    style Elasticsearch_68 fill:#7157A3,stroke:#523981,stroke-width:2px
    style Elasticsearch_56 fill:#D95C5C,stroke:#A13535,stroke-width:2px
```

## Proposals (High Level)

### Deploy PostgreSQL database for work coordination

The original requirement for no external data store is no longer required, and if we revist that we open a host of improvement that become trivial after switching to a PostgreSQL implementation.

- Real-time progress updates could be logged due to decoupling the target cluster under load from the data store.
- Remove Painless code that is nigh unmaintainable from the codebase, see [OpenSearchWorkCoordinator.java](https://github.com/opensearch-project/opensearch-migrations/blob/main/RFS/src/main/java/org/opensearch/migrations/bulkload/workcoordination/OpenSearchWorkCoordinator.java).
- Record throttling events or other distributed state that could be actioned by other workers.

```mermaid
sequenceDiagram
    title RFS Process
    participant sc as Source Cluster
    participant s3 as Snapshot Store (S3)
    participant rfs1 as RFS Worker
    participant tc as Target Cluster
    participant sql as PostgreSQL

    sc ->> s3: Create snapshot
    note over rfs1: Workers can vertical scale
    rfs1 ->> sql: Acquire work lease
    rfs1 ->> s3: Download snapshot
    rfs1 ->> tc: Reindex data
```

### Decouple Reindexing from the Snapshot

As outline above the RFS worker has many different responsibilities that can impact the ability to scale horizontally.  By pulling the responsibility of understanding the structure of the snapshot files we can drastically reshape how RFS scales.

```mermaid
sequenceDiagram
    title RFS Process
    participant sc as Source Cluster
    participant s3 as Snapshot Store (S3)
    participant sp as Snapshot Worker
    participant s3d as Document Store (S3)
    participant rfs1 as RFS Worker
    participant tc as Target Cluster
    participant sql as PostgreSQL

    sc ->> s3: Create snapshot
    note over sp: Workers can vertical scale
    sp ->> sql: Acquire work lease
    sp ->> s3: Read snapshot
    sp ->> s3d: Write document data
    note over rfs1: Workers can vertical scale
    rfs1 ->> sql: Acquire work lease
    rfs1 ->> s3d: Download document data
    rfs1 ->> tc: Reindex data
```

**Document Standard**

One of the reasons that we can decouple snapshot processing from RFS is there is only a small amount of information that is relevant to the reindexing process: the index id, shard id, document id, and document source.  This would allow us to adopt a simplified document standard.  Future win: this would allow migration of non-lucene data into OpenSearch via RFS.

```java
interface ReindexDocument {
    String indexName;
    String shardId;
    String documentId;
    JSONObject body;
}
```

**Storage Format**

It is not clear what the best format is for throughput and experimentation could prove this out; to start with it could be putting each document in its own s3 path `s3://bucket-name/{index-name}/{shard-id}/{document-id}.json` or using a fixed size chunked 100mb that is compressible.  This would make the runtime of the RFS workers much more deterministic.

**Reindexer document reader flexibility**

With the overhead of reading snapshot data there is an opportunity to change the algorithm we use to select the documents to reindex on.  Assuming that reading documents will always be faster than sending them for reindex, we could have the reindexer choose an algorithm that best suites the target cluster.

On a 'scale up' operation, if documents from a shard were to be reshard into two different shards on the new cluster, the cluster had to be responsible for diving up those items.  If instead the reindexer picked documents based on the new sharding algorithm we could ensure documents would only go from a single RFS worker onto a single destination node.


**Reshard with 1 to 4 Expansion minimal overhead**
```mermaid
graph TD
    subgraph Document Store
        scNode1[Shard1]
    end

    scNode1 --> shard1
    scNode1 --> shard2
    scNode1 --> shard3
    scNode1 --> shard4

    subgraph RFSWorker1
        shard1[Processing: Shard1<br>n % 4 = 0]
    end
    subgraph RFSWorker2
        shard2[Processing: Shard1<br>n % 4 = 1]
    end
    subgraph RFSWorker3
        shard3[Processing: Shard1<br>n % 4 = 2]
    end
    subgraph RFSWorker4
        shard4[Processing: Shard1<br>n % 4 = 3]
    end

    subgraph TargetCluster
        Node1
        Node2
        Node3
        Node4
    end

    shard1 -->|100% load| Node1
    shard2 -->|100% load| Node2
    shard3 -->|100% load| Node3
    shard4 -->|100% load| Node4
```


