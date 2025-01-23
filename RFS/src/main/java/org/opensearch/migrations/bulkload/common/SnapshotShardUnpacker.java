package org.opensearch.migrations.bulkload.common;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.util.Arrays;
import java.util.stream.Stream;

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
        printShards(luceneIndexDir, 1);
        var lucene6Jars = getJarUrls("lucene6");
        try (var lucene6Loader = new URLClassLoader(lucene6Jars, null)) {
            var upgraderClass = lucene6Loader.loadClass("org.opensearch.migrations.lucene6.Lucene6Upgrader");
            var upgraderInstance = upgraderClass.getDeclaredConstructor().newInstance();

            var method = upgraderClass.getMethod("upgradeIndex", String.class);
            method.invoke(upgraderInstance, luceneIndexDir.toString());
        } catch (Exception e) {
            log.atInfo().setMessage("Unable to upgrade with lucene6").setCause(e).log();
        }

        printShards(luceneIndexDir, 2);
        var lucene7Jars = getJarUrls("lucene7");
        try (var lucene7Loader = new URLClassLoader(lucene7Jars, null)) {
            var upgraderClass = lucene7Loader.loadClass("org.opensearch.migrations.lucene7.Lucene7Upgrader");
            var upgraderInstance = upgraderClass.getDeclaredConstructor().newInstance();

            var method = upgraderClass.getMethod("upgradeIndex", String.class);
            method.invoke(upgraderInstance, luceneIndexDir.toString());
        } catch (Exception e) {
            log.atInfo().setMessage("Unable to upgrade with lucene7").setCause(e).log();
        }

        printShards(luceneIndexDir, 3);
        var lucene8Jars = getJarUrls("lucene8");
        try (var lucene8Loader = new URLClassLoader(lucene8Jars, null)) {
            var upgraderClass = lucene8Loader.loadClass("org.opensearch.migrations.lucene8.Lucene8Upgrader");
            var upgraderInstance = upgraderClass.getDeclaredConstructor().newInstance();

            var method = upgraderClass.getMethod("upgradeIndex", String.class);
            method.invoke(upgraderInstance, luceneIndexDir.toString());
        } catch (Exception e) {
            log.atInfo().setMessage("Unable to upgrade with lucene8").setCause(e).log();
        }

        printShards(luceneIndexDir, 4);
        return luceneIndexDir;
    }

    @SneakyThrows
    private void printShards(Path indexDir, int num) {
        var dir = new File(indexDir.toString());
        var files = dir.listFiles((d, name) -> true);
        var newDir = new File(dir.getAbsolutePath() + "/" + num);
        newDir.mkdir();
  
        copyDirectory(indexDir, Path.of(indexDir.toString(), "..", "copy_"+num));
        log.atInfo()
            .setMessage("shard files: {}")
            .addArgument(files)
            .log();
    }

    @SneakyThrows
    public static void copyDirectory(Path source, Path target) {
        // Create the target directory if it doesn't exist
        if (!Files.exists(target)) {
            Files.createDirectories(target);
        }

        // Walk the file tree starting at 'source'
        try (Stream<Path> paths = Files.walk(source)) {
            // For each path encountered...
            paths.forEach(path -> {
                // Resolve the path relative to the source,
                // then resolve it against the target
                Path targetPath = target.resolve(source.relativize(path));

                try {
                    if (Files.isDirectory(path)) {
                        // Create directory if it doesn't exist
                        if (!Files.exists(targetPath)) {
                            Files.createDirectories(targetPath);
                        }
                    } else {
                        // Copy file, overwriting existing files
                        Files.copy(path, targetPath, StandardCopyOption.REPLACE_EXISTING);
                    }
                } catch (IOException e) {
                    // In a production setting, handle or log this exception properly
                    throw new RuntimeException("Error copying file " + path + " to " + targetPath, e);
                }
            });
        }
    }

    private URL[] getJarUrls(String subdir) {
        var dir = new File("build/" + subdir + "Libs");
        var jarFiles = dir.listFiles((d, name) -> name.endsWith(".jar"));
        log.atInfo().setMessage( subdir + " libs: {}").addArgument(jarFiles).log();
        var jarUrls = Arrays.stream(jarFiles)
                .map(f -> extracted(f))
                .toArray(URL[]::new);
        return jarUrls;
    } 
    private URL extracted(File f) {
        try {
            return f.toURI().toURL();
        } catch (MalformedURLException e) {
            throw new RuntimeException(e);
        }
    }

    public static class CouldNotUnpackShard extends RfsException {
        public CouldNotUnpackShard(String message, Exception e) {
            super(message, e);
        }
    }
    public static class CouldNotUpgradeShard extends RfsException {
        public CouldNotUpgradeShard(String message, Exception e) {
            super(message, e);
        }
    }
}
