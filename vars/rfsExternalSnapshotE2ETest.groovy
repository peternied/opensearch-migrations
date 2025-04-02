// Note: This integ test uses an external S3 snapshot instead of deploying a source cluster

def call(Map config = [:]) {
    def migrationContextId = 'migration-rfs-external-snapshot'
    def stageId = config.stageId ?: 'rfs-external-snapshot-integ'
    // Get the lock resource name from config or default to the stageId
    def lockResourceName = config.lockResourceName ?: stageId
    def sourceContextId = 'source-empty'
    
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
            "sourceCluster" : {
              "endpoint": "https://vpc-os-cluster-rfs-akurait-av2nwb2dagx7u3zf235z354xna.us-east-1.es.amazonaws.com",
              "version": "ES_7.10",
              "auth": {
                "type": "sigv4",
                "region": "us-east-1",
                "serviceSigningName": "es"
              }
            },
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
            "otelCollectorEnabled": true,
            "sourceClusterDisabled": true,
            "sourceClusterEndpoint": "dummy-endpoint-not-used"
          }
        }
    """
    defaultIntegPipeline(
            sourceContext: source_cdk_context,
            migrationContext: migration_cdk_context,
            sourceContextId: sourceContextId,
            migrationContextId: migrationContextId,
            defaultStageId: stageId,
            lockResourceName: lockResourceName,
            skipCaptureProxyOnNodeSetup: true,
            jobName: 'rfs-external-snapshot-e2e-test',
            integTestCommand: '/root/lib/integ_test/integ_test/s3_snapshot_tests.py',
            // Override the deploy step to use --skip-source-deploy flag
            deployStep: {
                // Use the actual stage parameter for deployment, not the lock variable
                def deployStage = params.STAGE
                echo "Acquired lock resource: ${lockVar}"
                echo "Deploying with stage: ${deployStage}"
                sh 'sudo usermod -aG docker $USER'
                sh 'sudo newgrp docker'
                
                // Use hardcoded file names and context IDs
                def sourceContextFileName = 'sourceJenkinsContext.json'
                def migrationContextFileName = 'migrationJenkinsContext.json'
                
                def baseCommand = "sudo --preserve-env ./awsE2ESolutionSetup.sh --source-context-file './${sourceContextFileName}' " +
                        "--migration-context-file './${migrationContextFileName}' " +
                        "--source-context-id ${sourceContextId} " +
                        "--migration-context-id ${migrationContextId} " +
                        "--stage ${deployStage} " +
                        "--migrations-git-url ${params.GIT_REPO_URL} " +
                        "--migrations-git-branch ${params.GIT_BRANCH} " +
                        "--skip-source-deploy" // Skip deploying the source cluster
                
                withCredentials([string(credentialsId: 'migrations-test-account-id', variable: 'MIGRATIONS_TEST_ACCOUNT_ID')]) {
                    withAWS(role: 'JenkinsDeploymentRole', roleAccount: "${MIGRATIONS_TEST_ACCOUNT_ID}", duration: 5400, roleSessionName: 'jenkins-session') {
                        sh baseCommand
                    }
                }
            },
            // Override the finish step to avoid the FilePath error
            finishStep: {
                echo "External snapshot test completed"
            }
    )
}
