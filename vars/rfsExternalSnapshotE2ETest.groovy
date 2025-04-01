// E2E test for RFS using an external S3 snapshot instead of deploying a source cluster

def call(Map config = [:]) {
    def migrationContextId = 'migration-rfs-external-snapshot'
    def stageId = config.stageId ?: 'rfs-external-snapshot-integ'
    // Get the lock resource name from config or default to the stageId
    def lockResourceName = config.lockResourceName ?: stageId
    
    // No source_cdk_context as we're using an external S3 snapshot instead
    
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
            // No sourceContext as we're not deploying a source cluster
            migrationContext: migration_cdk_context,
            // No sourceContextId as we're not deploying a source cluster
            migrationContextId: migrationContextId,
            defaultStageId: stageId,
            lockResourceName: lockResourceName,  // Use the lock resource name for Jenkins locks
            skipSourceDeployment: true, // Skip deploying a source cluster
            skipCaptureProxyOnNodeSetup: true,
            jobName: 'rfs-external-snapshot-e2e-test',
            integTestCommand: '/root/lib/integ_test/integ_test/s3_snapshot_tests.py',
    )
}
