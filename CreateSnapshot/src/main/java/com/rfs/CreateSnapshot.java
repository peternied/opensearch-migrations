package com.rfs;

import com.beust.jcommander.JCommander;
import com.beust.jcommander.Parameter;
import com.beust.jcommander.ParameterException;
import com.beust.jcommander.ParametersDelegate;

import lombok.AllArgsConstructor;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;

import com.rfs.common.FileSystemSnapshotCreator;
import com.rfs.common.OpenSearchClient;
import com.rfs.common.S3SnapshotCreator;
import com.rfs.common.SnapshotCreator;
import com.rfs.common.SourceRepo;
import com.rfs.common.TryHandlePhaseFailure;
import com.rfs.worker.SnapshotRunner;

import java.util.function.Function;

@Slf4j
public class CreateSnapshot {
    public static class Args {
        @Parameter(names = {"--snapshot-name"},
                required = true,
                description = "The name of the snapshot to migrate")
        public String snapshotName;

        @ParametersDelegate
        public SourceRepo.Params sourceRepo;

        @Parameter(names = {"--source-host"},
                required = true,
                description = "The source host and port (e.g. http://localhost:9200)")
        public String sourceHost;

        @Parameter(names = {"--source-username"},
                description = "Optional.  The source username; if not provided, will assume no auth on source")
        public String sourceUser = null;

        @Parameter(names = {"--source-password"},
                description = "Optional.  The source password; if not provided, will assume no auth on source")
        public String sourcePass = null;

        @Parameter(names = {"--source-insecure"},
                description = "Allow untrusted SSL certificates for source")
        public boolean sourceInsecure = false;

        @Parameter(names = {"--no-wait"}, description = "Optional.  If provided, the snapshot runner will not wait for completion")
        public boolean noWait = false;

        @Parameter(names = {"--max-snapshot-rate-mb-per-node"},
                required = false,
                description = "The maximum snapshot rate in megabytes per second per node")
        public Integer maxSnapshotRateMBPerNode;
    }

    @Getter
    @AllArgsConstructor
    public static class S3RepoInfo {
        String awsRegion;
        String repoUri;
    }

    public static void main(String[] args) throws Exception {
        // Grab out args
        Args arguments = new Args();
        JCommander.newBuilder()
                .addObject(arguments)
                .build()
                .parse(args);

        log.info("Running CreateSnapshot with {}", String.join(" ", args));
        arguments.sourceRepo.validate();

        run(c -> ((arguments.sourceRepo.getFileSystemRepoPath() != null)
                        ? new FileSystemSnapshotCreator(arguments.snapshotName, c, arguments.sourceRepo.getFileSystemRepoPath())
                        : new S3SnapshotCreator(arguments.snapshotName, c, arguments.sourceRepo.getS3RepoUri(), arguments.sourceRepo.getS3Region(), arguments.maxSnapshotRateMBPerNode)),
                new OpenSearchClient(arguments.sourceHost, arguments.sourceUser, arguments.sourcePass, arguments.sourceInsecure),
                arguments.noWait
        );
    }

    public static void run(Function<OpenSearchClient, SnapshotCreator> snapshotCreatorFactory,
                           OpenSearchClient openSearchClient, boolean noWait) throws Exception {
        TryHandlePhaseFailure.executeWithTryCatch(() -> {
            if (noWait) {
                SnapshotRunner.run(snapshotCreatorFactory.apply(openSearchClient));
            } else {
                SnapshotRunner.runAndWaitForCompletion(snapshotCreatorFactory.apply(openSearchClient));
            }
        });
    }
}


