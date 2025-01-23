package org.opensearch.migrations.bulkload.common;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import org.opensearch.migrations.LuceneUpgrader;
import org.opensearch.migrations.bulkload.models.ShardFileInfo;
import org.opensearch.migrations.bulkload.models.ShardMetadata;

import lombok.RequiredArgsConstructor;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.apache.lucene.store.FSDirectory;
import org.apache.lucene.store.IOContext;
import org.apache.lucene.store.IndexOutput;
import org.apache.lucene.store.NativeFSLockFactory;
import org.apache.lucene.util.BytesRef;

@RequiredArgsConstructor
@Slf4j
public class SnapshotShardUnpacker {
    private final SourceRepoAccessor repoAccessor;
    private final Path luceneFilesBasePath;
    private final ShardMetadata shardMetadata;
    private final int bufferSize;

    @RequiredArgsConstructor
    public static class Factory {
        private final SourceRepoAccessor repoAccessor;
        private final Path luceneFilesBasePath;
        private final int bufferSize;

        public SnapshotShardUnpacker create(ShardMetadata shardMetadata) {
            return new SnapshotShardUnpacker(repoAccessor, luceneFilesBasePath, shardMetadata, bufferSize);
        }
    }

    public Path unpack() {
        // Create the directory for the shard's lucene files
        var luceneIndexDir = Paths.get(
            luceneFilesBasePath + "/" + shardMetadata.getIndexName() + "/" + shardMetadata.getShardId()
        );
        try {
            // Some constants
            NativeFSLockFactory lockFactory = NativeFSLockFactory.INSTANCE;

            // Ensure the blob files are prepped, if they need to be
            repoAccessor.prepBlobFiles(shardMetadata);

            Files.createDirectories(luceneIndexDir);
            try (FSDirectory primaryDirectory = FSDirectory.open(luceneIndexDir, lockFactory)) {
                for (ShardFileInfo fileMetadata : shardMetadata.getFiles()) {
                    log.atInfo().setMessage("Unpacking - Blob Name: {}, Lucene Name: {}")
                        .addArgument(fileMetadata::getName)
                        .addArgument(fileMetadata::getPhysicalName)
                        .log();
                    try (
                        IndexOutput indexOutput = primaryDirectory.createOutput(
                            fileMetadata.getPhysicalName(),
                            IOContext.DEFAULT
                        );
                    ) {
                        if (fileMetadata.getName().startsWith("v__")) {
                            final BytesRef hash = fileMetadata.getMetaHash();
                            indexOutput.writeBytes(hash.bytes, hash.offset, hash.length);
                        } else {
                            try (
                                InputStream stream = new PartSliceStream(
                                    repoAccessor,
                                    fileMetadata,
                                    shardMetadata.getIndexId(),
                                    shardMetadata.getShardId()
                                )
                            ) {
                                final byte[] buffer = new byte[Math.toIntExact(
                                    Math.min(bufferSize, fileMetadata.getLength())
                                )];
                                int length;
                                while ((length = stream.read(buffer)) > 0) {
                                    indexOutput.writeBytes(buffer, 0, length);
                                }
                            }
                        }
                    }
                }
            }
        } catch (Exception e) {
            throw new CouldNotUnpackShard(
                "Could not unpack shard: Index " + shardMetadata.getIndexId() + ", Shard " + shardMetadata.getShardId(),
                e
            );
        }
        
        upgradeWithLuceneVersion("lucene6", luceneIndexDir);
        upgradeWithLuceneVersion("lucene7", luceneIndexDir);
        upgradeWithLuceneVersion("lucene8", luceneIndexDir);
        return luceneIndexDir;
    }

    private void upgradeWithLuceneVersion(String version, Path indexDir) {
        var luceneJars = getJarUrls(version);
        try (var classLoader = new URLClassLoader(luceneJars, Thread.currentThread().getContextClassLoader())) {
            Thread.currentThread().setContextClassLoader(classLoader);
            for (URL url : classLoader.getURLs()) {
                System.out.println("Loaded URL: " + url);
            }
            var upgraderClass = classLoader.loadClass("org.opensearch.migrations." + version + ".Lucene" + version.substring(version.length() - 1) + "Upgrader");
            var upgraderInstance = (LuceneUpgrader) upgraderClass.getDeclaredConstructor().newInstance();

            upgraderInstance.upgradeIndex(indexDir.toString());
        } catch (Exception e) {
            log.atInfo()
                .setMessage("Unable to upgrade with {}: {}")
                .addArgument(version)
                .addArgument(e.getMessage())
                .setCause(e)
                .log();
        }
    }

    @SneakyThrows
    private URL[] getJarUrls(String version) {
        var jarListFile = Path.of("build/luceneJarPaths", version + ".txt");
        var jarUrls = Files.readAllLines(jarListFile)
            .stream()
            .map(jarPath -> {
                try {
                    return Path.of(jarPath).toUri().toURL();
                } catch (Exception e) {
                    throw new RuntimeException("Failed to convert path to URL: " + jarPath, e);
                }
            })
            .collect(Collectors.toList());
        return jarUrls.toArray(new URL[0]);
    }

    public static class CouldNotUnpackShard extends RfsException {
        public CouldNotUnpackShard(String message, Exception e) {
            super(message, e);
        }
    }
}
