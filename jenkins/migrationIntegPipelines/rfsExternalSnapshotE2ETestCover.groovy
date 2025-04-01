def gitBranch = params.GIT_BRANCH ?: 'JenkinsLargeSnapshotMigration'
def gitUrl = params.GIT_REPO_URL ?: 'https://github.com/AndreKurait/opensearch-migrations.git'

library identifier: "migrations-lib@${gitBranch}", retriever: modernSCM(
        [$class: 'GitSCMSource',
         remote: "${gitUrl}"])

// Shared library function (location from root: vars/rfsExternalSnapshotE2ETest.groovy)
// Use rfs-integ as the lock resource name to reuse the existing lock resource
// But use the actual STAGE parameter as the deployment stage for CDK context
rfsExternalSnapshotE2ETest([
    stageId: params.STAGE,            // Keep this for backward compatibility
    lockResourceName: 'rfs-integ',    // Use existing lock resource name for Jenkins locks
    deploymentStage: params.STAGE     // Use the actual stage parameter for CDK deployments
])
