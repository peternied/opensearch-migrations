def gitBranch = params.GIT_BRANCH ?: 'JenkinsLargeSnapshotMigration'
def gitUrl = params.GIT_REPO_URL ?: 'https://github.com/AndreKurait/opensearch-migrations.git'

library identifier: "migrations-lib@${gitBranch}", retriever: modernSCM(
        [$class: 'GitSCMSource',
         remote: "${gitUrl}"])

// Shared library function that uses an external S3 snapshot rather than a source cluster
// Always use rfs-external-snapshot as the lock resource name regardless of the stage parameter
// But use the actual STAGE parameter as the deployment stage for CDK context
rfsExternalSnapshotE2ETest([
    stageId: params.STAGE,            // Keep this for backward compatibility
    lockResourceName: 'rfs-external-snapshot',    // Use fixed resource name for Jenkins locks
    deploymentStage: params.STAGE     // Use the actual stage parameter for CDK deployments
])
