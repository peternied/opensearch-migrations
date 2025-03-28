def gitBranch = params.GIT_BRANCH ?: 'JenkinsLargeSnapshotMigration'
def gitUrl = params.GIT_REPO_URL ?: 'https://github.com/AndreKurait/opensearch-migrations.git'

library identifier: "migrations-lib@${gitBranch}", retriever: modernSCM(
        [$class: 'GitSCMSource',
         remote: "${gitUrl}"])

// Shared library function (location from root: vars/rfsDefaultE2ETest.groovy)
// Always use rfs-integ as the lock resource name regardless of the stage parameter
// But use the actual STAGE parameter as the deployment stage for CDK context
rfsDefaultE2ETest([
    stageId: params.STAGE,            // Keep this for backward compatibility
    lockResourceName: 'rfs-integ',    // Use fixed resource name for Jenkins locks
    deploymentStage: params.STAGE     // Use the actual stage parameter for CDK deployments
])
