import {Effect, PolicyStatement, Role, ServicePrincipal} from "aws-cdk-lib/aws-iam";
import {Construct} from "constructs";
import {CpuArchitecture} from "aws-cdk-lib/aws-ecs";
import {RemovalPolicy} from "aws-cdk-lib";
import { IApplicationLoadBalancer } from "aws-cdk-lib/aws-elasticloadbalancingv2";
import { ICertificate } from "aws-cdk-lib/aws-certificatemanager";
import { IStringParameter, StringParameter } from "aws-cdk-lib/aws-ssm";

export function createOpenSearchIAMAccessPolicy(partition: string, region: string, accountId: string): PolicyStatement {
    return new PolicyStatement({
        effect: Effect.ALLOW,
        resources: [`arn:${partition}:es:${region}:${accountId}:domain/*`],
        actions: [
            "es:ESHttp*"
        ]
    })
}

export function createOpenSearchServerlessIAMAccessPolicy(partition: string, region: string, accountId: string): PolicyStatement {
    return new PolicyStatement({
        effect: Effect.ALLOW,
        resources: [`arn:${partition}:aoss:${region}:${accountId}:collection/*`],
        actions: [
            "aoss:APIAccessAll"
        ]
    })
}

export function createMSKConsumerIAMPolicies(scope: Construct, partition: string, region: string, accountId: string, stage: string, deployId: string): PolicyStatement[] {
    const mskClusterARN = getMigrationStringParameterValue(scope, { parameter: MigrationSSMParameter.MSK_CLUSTER_ARN, stage, defaultDeployId: deployId });
    const mskClusterName = getMigrationStringParameterValue(scope, { parameter: MigrationSSMParameter.MSK_CLUSTER_NAME, stage, defaultDeployId: deployId });
    const mskClusterConnectPolicy = new PolicyStatement({
        effect: Effect.ALLOW,
        resources: [mskClusterARN],
        actions: [
            "kafka-cluster:Connect"
        ]
    })
    const mskClusterAllTopicArn = `arn:${partition}:kafka:${region}:${accountId}:topic/${mskClusterName}/*`
    const mskTopicConsumerPolicy = new PolicyStatement({
        effect: Effect.ALLOW,
        resources: [mskClusterAllTopicArn],
        actions: [
            "kafka-cluster:DescribeTopic",
            "kafka-cluster:ReadData"
        ]
    })
    const mskClusterAllGroupArn = `arn:${partition}:kafka:${region}:${accountId}:group/${mskClusterName}/*`
    const mskConsumerGroupPolicy = new PolicyStatement({
        effect: Effect.ALLOW,
        resources: [mskClusterAllGroupArn],
        actions: [
            "kafka-cluster:AlterGroup",
            "kafka-cluster:DescribeGroup"
        ]
    })
    return [mskClusterConnectPolicy, mskTopicConsumerPolicy, mskConsumerGroupPolicy]

}

export function createMSKProducerIAMPolicies(scope: Construct, partition: string, region: string, accountId: string, stage: string, deployId: string): PolicyStatement[] {
    const mskClusterARN = getMigrationStringParameterValue(scope, { parameter: MigrationSSMParameter.MSK_CLUSTER_ARN, stage, defaultDeployId: deployId });
    const mskClusterName = getMigrationStringParameterValue(scope, { parameter: MigrationSSMParameter.MSK_CLUSTER_NAME, stage, defaultDeployId: deployId });
    const mskClusterConnectPolicy = new PolicyStatement({
        effect: Effect.ALLOW,
        resources: [mskClusterARN],
        actions: [
            "kafka-cluster:Connect"
        ]
    })
    const mskClusterAllTopicArn = `arn:${partition}:kafka:${region}:${accountId}:topic/${mskClusterName}/*`
    const mskTopicProducerPolicy = new PolicyStatement({
        effect: Effect.ALLOW,
        resources: [mskClusterAllTopicArn],
        actions: [
            "kafka-cluster:CreateTopic",
            "kafka-cluster:DescribeTopic",
            "kafka-cluster:WriteData"
        ]
    })
    return [mskClusterConnectPolicy, mskTopicProducerPolicy]
}

export function createAwsDistroForOtelPushInstrumentationPolicy(): PolicyStatement {
    // see https://aws-otel.github.io/docs/setup/permissions
    return new PolicyStatement( {
        effect: Effect.ALLOW,
        resources: ["*"],
        actions: [
            "logs:PutLogEvents",
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:DescribeLogStreams",
            "logs:DescribeLogGroups",
            "logs:PutRetentionPolicy",
            "xray:PutTraceSegments",
            "xray:PutTelemetryRecords",
            "xray:GetSamplingRules",
            "xray:GetSamplingTargets",
            "xray:GetSamplingStatisticSummaries",
            "ssm:GetParameters"
        ]
    })
}

export function createDefaultECSTaskRole(scope: Construct, serviceName: string): Role {
    const serviceTaskRole = new Role(scope, `${serviceName}-TaskRole`, {
        assumedBy: new ServicePrincipal('ecs-tasks.amazonaws.com'),
        description: 'ECS Service Task Role'
    });
    // Add default Task Role policy to allow exec and writing logs
    serviceTaskRole.addToPolicy(new PolicyStatement({
        effect: Effect.ALLOW,
        resources: ['*'],
        actions: [
            "logs:CreateLogGroup",
            "logs:CreateLogStream",
            "logs:DescribeLogGroups",
            "logs:DescribeLogStreams",
            "logs:PutLogEvents",
            "ssmmessages:CreateControlChannel",
            "ssmmessages:CreateDataChannel",
            "ssmmessages:OpenControlChannel",
            "ssmmessages:OpenDataChannel"
        ]
    }))
    return serviceTaskRole
}

export function validateFargateCpuArch(cpuArch?: string): CpuArchitecture {
    const desiredArch = cpuArch ? cpuArch : process.arch
    const desiredArchUpper = desiredArch.toUpperCase()

    if (desiredArchUpper === "X86_64" || desiredArchUpper === "X64") {
        return CpuArchitecture.X86_64
    } else if (desiredArchUpper === "ARM64") {
        return CpuArchitecture.ARM64
    } else {
        if (cpuArch) {
            throw new Error(`Unknown Fargate cpu architecture provided: ${desiredArch}`)
        }
        else {
            throw new Error(`Unsupported process cpu architecture detected: ${desiredArch}, CDK requires X64 or ARM64 for Docker image compatability`)
        }
    }
}

export function parseRemovalPolicy(optionName: string, policyNameString?: string): RemovalPolicy|undefined {
    const policy = policyNameString ? RemovalPolicy[policyNameString as keyof typeof RemovalPolicy] : undefined
    if (policyNameString && !policy) {
        throw new Error(`Provided '${optionName}' with value '${policyNameString}' does not match a selectable option, for reference https://docs.aws.amazon.com/cdk/api/v2/docs/aws-cdk-lib.RemovalPolicy.html`)
    }
    return policy
}


export type ALBConfig = NewALBListenerConfig;

export interface NewALBListenerConfig {
    alb: IApplicationLoadBalancer,
    albListenerCert: ICertificate,
    albListenerPort?: number,
}

export function isNewALBListenerConfig(config: ALBConfig): config is NewALBListenerConfig {
    const parsed = config as NewALBListenerConfig;
    return parsed.alb !== undefined && parsed.albListenerCert !== undefined;
}


export interface MigrationSSMConfig {
    parameter: MigrationSSMParameter,
    stage: string,
    defaultDeployId: string
}

export function createMigrationStringParameter(scope: Construct, stringValue: string, props: MigrationSSMConfig) {
    return new StringParameter(scope, `SSMParameter${props.parameter.charAt(0).toUpperCase() + props.parameter.slice(1)}`, {
        parameterName: getMigrationStringParameterName(props),
        stringValue: stringValue,
        description: `Opensearch migration SSM parameter for ${props.parameter} with stage ${props.stage} and deploy id ${props.defaultDeployId}`,
    });
}

export function getMigrationStringParameter(scope: Construct, props: MigrationSSMConfig): IStringParameter {
    return StringParameter.fromStringParameterName(scope, `SSMParameter${props.parameter.charAt(0).toUpperCase() + props.parameter.slice(1)}`,
        getMigrationStringParameterName(props));
}

export function getMigrationStringParameterValue(scope: Construct, props: MigrationSSMConfig): string {
    return StringParameter.valueForTypedStringParameterV2(scope, getMigrationStringParameterName(props));
}

export function getCustomStringParameterValue(scope: Construct, parameterName: string): string {
    return StringParameter.valueForTypedStringParameterV2(scope, parameterName);
}

export function getMigrationStringParameterName(props: MigrationSSMConfig): string {
    return `/migration/${props.stage}/${props.defaultDeployId}/${props.parameter}`;
}

export enum MigrationSSMParameter {
    MIGRATION_API_URL = 'albMigrationApiUrl',
    MIGRATION_API_URL_ALIAS = 'albMigrationApiUrlAlias',
    SOURCE_PROXY_URL = 'albSourceProxyUrl',
    SOURCE_PROXY_URL_ALIAS = 'albSourceProxyUrlAlias',
    TARGET_PROXY_URL = 'albTargetProxyUrl',
    TARGET_PROXY_URL_ALIAS = 'albTargetProxyUrlAlias',
    MIGRATION_LISTENER_URL = 'albMigrationListenerUrl',
    MIGRATION_LISTENER_URL_ALIAS = 'albMigrationListenerUrlAlias',
    ARTIFACT_S3_ARN = 'artifactS3Arn',
    FETCH_MIGRATION_COMMAND = 'fetchMigrationCommand',
    FETCH_MIGRATION_TASK_DEF_ARN = 'fetchMigrationTaskDefArn',
    FETCH_MIGRATION_TASK_EXEC_ROLE_ARN = 'fetchMigrationTaskExecRoleArn',
    FETCH_MIGRATION_TASK_ROLE_ARN = 'fetchMigrationTaskRoleArn',
    KAFKA_BROKERS = 'kafkaBrokers',
    MSK_CLUSTER_ARN = 'mskClusterARN',
    MSK_CLUSTER_NAME = 'mskClusterName',
    OS_ACCESS_SECURITY_GROUP_ID = 'osAccessSecurityGroupId',
    OS_CLUSTER_ENDPOINT = 'osClusterEndpoint',
    OS_USER_AND_SECRET_ARN = 'osUserAndSecretArn',
    OSI_PIPELINE_LOG_GROUP_NAME = 'osiPipelineLogGroupName',
    OSI_PIPELINE_ROLE_ARN = 'osiPipelineRoleArn',
    REPLAYER_OUTPUT_ACCESS_SECURITY_GROUP_ID = 'replayerOutputAccessSecurityGroupId',
    REPLAYER_OUTPUT_EFS_ID = 'replayerOutputEfsId',
    SOURCE_CLUSTER_ENDPOINT = 'sourceClusterEndpoint',
    SERVICE_SECURITY_GROUP_ID = 'serviceSecurityGroupId',
    SERVICES_YAML_FILE = 'servicesYamlFile',
    TRAFFIC_STREAM_SOURCE_ACCESS_SECURITY_GROUP_ID = 'trafficStreamSourceAccessSecurityGroupId',
    VPC_ID = 'vpcId',
}
