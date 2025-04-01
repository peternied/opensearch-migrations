// Note: This integ test uses an external S3 snapshot instead of deploying a source cluster

def call(Map config = [:]) {
    def migrationContextId = 'migration-rfs-external-snapshot'
    def stageId = config.stageId ?: 'rfs-external-snapshot-integ'
    // Get the lock resource name from config or default to the stageId
    def lockResourceName = config.lockResourceName ?: stageId
    
    // Empty source context to satisfy defaultIntegPipeline requirements
    def source_cdk_context = """
        {
          "source-empty": {
            "suffix": "ec2-source-<STAGE>",
            "networkStackSuffix": "ec2-source-<STAGE>"
          }
        }
    """
    
    def migration_cdk_context = """
        {
          "migration-rfs-external-snapshot": {
            "stage": "<STAGE>",
            "vpcId": "<VPC_ID>",
            "engineVersion": "OS_2.11",
            "domainName": "os-cluster-<STAGE>",
            "dataNodeCount": 2,
            "openAccessPolicyEnabled": true,
            "domainRemovalPolicy": "DESTROY",
            "artifactBucketRemovalPolicy": "DESTROY",
            "trafficReplayerServiceEnabled": false,
            "reindexFromSnapshotServiceEnabled": true,
            "tlsSecurityPolicy": "TLS_1_2",
            "enforceHTTPS": true,
            "nodeToNodeEncryptionEnabled": true,
            "encryptionAtRestEnabled": true,
            "vpcEnabled": true,
            "vpcAZCount": 2,
            "domainAZCount": 2,
            "mskAZCount": 2,
            "migrationAssistanceEnabled": true,
            "replayerOutputEFSRemovalPolicy": "DESTROY",
            "migrationConsoleServiceEnabled": true,
            "otelCollectorEnabled": true
          }
        }
    """

    defaultIntegPipeline(
            sourceContext: source_cdk_context,
            migrationContext: migration_cdk_context,
            sourceContextId: 'source-empty',
            migrationContextId: migrationContextId,
            defaultStageId: stageId,
            lockResourceName: lockResourceName,
            skipCaptureProxyOnNodeSetup: true,
            jobName: 'rfs-external-snapshot-e2e-test',
            integTestCommand: '/root/lib/integ_test/integ_test/s3_snapshot_tests.py',
            // Override the deploy step to use --skip-source-deploy flag
            deployStep: { script ->
                script.dir('test') {
                    def deployStage = script.params.STAGE
                    script.echo "Acquired lock resource: ${script.lockVar}"
                    script.echo "Deploying with stage: ${deployStage}"
                    script.sh 'sudo usermod -aG docker $USER'
                    script.sh 'sudo newgrp docker'
                    def baseCommand = "sudo --preserve-env ./awsE2ESolutionSetup.sh --source-context-file './${script.source_context_file_name}' " +
                            "--migration-context-file './${script.migration_context_file_name}' " +
                            "--source-context-id ${script.source_context_id} " +
                            "--migration-context-id ${script.migration_context_id} " +
                            "--stage ${deployStage} " +
                            "--migrations-git-url ${script.params.GIT_REPO_URL} " +
                            "--migrations-git-branch ${script.params.GIT_BRANCH} " +
                            "--skip-source-deploy" // Skip deploying the source cluster
                    
                    script.withCredentials([script.string(credentialsId: 'migrations-test-account-id', variable: 'MIGRATIONS_TEST_ACCOUNT_ID')]) {
                        script.withAWS(role: 'JenkinsDeploymentRole', roleAccount: "${script.MIGRATIONS_TEST_ACCOUNT_ID}", duration: 5400, roleSessionName: 'jenkins-session') {
                            script.sh baseCommand
                        }
                    }
                }
            },
            // Override the finish step to avoid the FilePath error
            finishStep: { script ->
                script.echo "External snapshot test completed"
            }
    )
}
