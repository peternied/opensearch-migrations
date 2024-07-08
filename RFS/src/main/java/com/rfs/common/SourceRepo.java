package com.rfs.common;

import java.nio.file.Path;

import com.beust.jcommander.Parameter;
import com.beust.jcommander.ParameterException;

import lombok.Getter;

public interface SourceRepo {
    public Path getRepoRootDir();
    public Path getSnapshotRepoDataFilePath();
    public Path getGlobalMetadataFilePath(String snapshotId);
    public Path getSnapshotMetadataFilePath(String snapshotId);
    public Path getIndexMetadataFilePath(String indexId, String indexFileId);
    public Path getShardDirPath(String indexId, int shardId);
    public Path getShardMetadataFilePath(String snapshotId, String indexId, int shardId);
    public Path getBlobFilePath(String indexId, int shardId, String blobName);

    /*
    * Performs any work necessary to facilitate access to a given shard's blob files.  Depending on the implementation,
    * may involve no work at all, bulk downloading objects from a remote source, or any other operations.
    */
    public void prepBlobFiles(ShardMetadata.Data shardMetadata);

    @Getter
    public static class Params {  
        @Parameter(names = {"--file-system-repo-path"}, required = false, description = "The full path to the snapshot repo on the file system.")
        String fileSystemRepoPath;
    
        @Parameter(names = {"--s3-local-dir"}, description = "The absolute path to the directory on local disk to download S3 files to", required = false)
        String s3LocalDirPath;
    
        @Parameter(names = {"--s3-repo-uri"}, description = "The S3 URI of the snapshot repo, like: s3://my-bucket/dir1/dir2", required = false)
        String s3RepoUri;
    
        @Parameter(names = {"--s3-region"}, description = "The AWS Region the S3 bucket is in, like: us-east-2", required = false)
        String s3Region;

        public void validate() {
            if (fileSystemRepoPath == null && s3RepoUri == null) {
                throw new ParameterException("Either file-system-repo-path or s3-repo-uri must be set");
            }
            if (fileSystemRepoPath != null && s3RepoUri != null) {
                throw new ParameterException("Only one of file-system-repo-path and s3-repo-uri can be set");
            }
            if (s3RepoUri != null && s3Region == null) {
                throw new ParameterException("If an s3 repo is being used, s3-region must be set");
            }
        }
    
        public SourceRepo getRepo() {
            validate();           

            if ((s3RepoUri != null) && (s3Region == null || s3LocalDirPath == null)) {
                throw new ParameterException("If an s3 repo is being used, s3-region and s3-local-dir-path must be set");
            }

            return fileSystemRepoPath != null
                ? new FileSystemRepo(Path.of(fileSystemRepoPath))
                : S3Repo.create(Path.of(s3LocalDirPath), new S3Uri(s3RepoUri), s3Region);
        }
    }
}
