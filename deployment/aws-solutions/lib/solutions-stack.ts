import { Aws, CfnCondition, CfnMapping, CfnParameter, Fn, Stack, StackProps, Tags } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {
    BlockDeviceVolume,
    CloudFormationInit,
    InitCommand,
    InitElement,
    InitFile,
    Instance,
    InstanceClass,
    InstanceSize,
    InstanceType,
    IpAddresses,
    MachineImage,
    SubnetType,
    Vpc
} from "aws-cdk-lib/aws-ec2";
import { InstanceProfile, ManagedPolicy, Role, ServicePrincipal } from "aws-cdk-lib/aws-iam";
import { CfnDocument } from "aws-cdk-lib/aws-ssm";
import { Application, AttributeGroup } from "@aws-cdk/aws-servicecatalogappregistry-alpha";
import { createHash } from 'crypto';

export interface SolutionsInfrastructureStackProps extends StackProps {
    readonly solutionId: string;
    readonly solutionName: string;
    readonly solutionVersion: string;
    readonly codeBucket: string;
    readonly useExistingVpc: boolean;
}

export function applyAppRegistry(stack: Stack, stage: string, infraProps: SolutionsInfrastructureStackProps): string {
    const application = new Application(stack, "AppRegistry", {
        applicationName: Fn.join("-", [
            infraProps.solutionName,
            Aws.REGION,
            Aws.ACCOUNT_ID,
            stage
        ]),
        description: `Service Catalog application to track and manage all your resources for the solution ${infraProps.solutionName}`,
    });
    application.associateApplicationWithStack(stack);
    Tags.of(application).add("Solutions:SolutionID", infraProps.solutionId);
    Tags.of(application).add("Solutions:SolutionName", infraProps.solutionName);
    Tags.of(application).add("Solutions:SolutionVersion", infraProps.solutionVersion);
    Tags.of(application).add("Solutions:ApplicationType", "AWS-Solutions");

    const attributeGroup = new AttributeGroup(
        stack,
        "DefaultApplicationAttributes",
        {
            attributeGroupName: Fn.join("-", [
                Aws.REGION,
                stage,
                "attributes"
            ]),
            description: "Attribute group for solution information",
            attributes: {
                applicationType: "AWS-Solutions",
                version: infraProps.solutionVersion,
                solutionID: infraProps.solutionId,
                solutionName: infraProps.solutionName,
            },
        }
    );
    attributeGroup.associateWith(application)
    return application.applicationArn
}

export class SolutionsInfrastructureStack extends Stack {

    constructor(scope: Construct, id: string, props: SolutionsInfrastructureStackProps) {
        super(scope, id, props);
        this.templateOptions.templateFormatVersion = '2010-09-09';
        new CfnMapping(this, 'Solution', {
            mapping: {
                Config: {
                    CodeVersion: props.solutionVersion,
                    KeyPrefix: `${props.solutionName}/${props.solutionVersion}`,
                    S3Bucket: props.codeBucket,
                    SendAnonymousUsage: 'No',
                    SolutionId: props.solutionId
                }
            },
            lazy: false,
        });

        const stageParameter = new CfnParameter(this, 'Stage', {
            type: 'String',
            description: 'Specify the stage identifier which will be used in naming resources, e.g. dev,gamma,wave1',
            default: 'dev',
            noEcho: false
        });

        const appRegistryAppARN = applyAppRegistry(this, stageParameter.valueAsString, props)

        if (!props.useExistingVpc) {
            const vpcIdParam = new CfnParameter(this, 'VpcId', {
                type: 'AWS::EC2::VPC::Id',
                description: 'The ID of the existing VPC',
            });

            const subnetIdsParam = new CfnParameter(this, 'SubnetIds', {
                type: 'List<AWS::EC2::Subnet::Id>',
                description: 'List of subnet IDs in the VPC',
            });

            const availabilityZonesParam = new CfnParameter(this, 'AvailabilityZones', {
                type: 'List<String>',
                description: 'List of availability zones for the subnets',
            });
            /** TODO: Figure out how to handle user provided Vpc */
        }

        const vpc = new Vpc(this, 'Vpc', {
            // IP space should be customized for use cases that have specific IP range needs
            ipAddresses: IpAddresses.cidr('10.0.0.0/16'),
            maxAzs: 1,
            subnetConfiguration: [
                // Outbound internet access for private subnets require a NAT Gateway which must live in
                // a public subnet
                {
                    name: 'public-subnet',
                    subnetType: SubnetType.PUBLIC,
                    cidrMask: 24,
                },
                {
                    name: 'private-subnet',
                    subnetType: SubnetType.PRIVATE_WITH_EGRESS,
                    cidrMask: 24,
                },
            ],
        });

        new CfnDocument(this, "BootstrapShellDoc", {
            name: `SSM-${stageParameter.valueAsString}-BootstrapShell`,
            documentType: "Session",
            content: {
                "schemaVersion": "1.0",
                "description": "Document to hold regional settings for Session Manager",
                "sessionType": "Standard_Stream",
                "inputs": {
                    "cloudWatchLogGroupName": "",
                    "cloudWatchEncryptionEnabled": true,
                    "cloudWatchStreamingEnabled": false,
                    "kmsKeyId": "",
                    "runAsEnabled": false,
                    "runAsDefaultUser": "",
                    "idleSessionTimeout": "60",
                    "maxSessionDuration": "",
                    "shellProfile": {
                        "linux": "cd /opensearch-migrations && sudo -s"
                    }
                }
            }
        })

        const reindexFromSnapshotParam = new CfnParameter(this, "ReindexFromSnapshot", {
            description: "Backfill via reindex from snapshot is enabled in the Migration Console",
            default: 'Enabled',
            allowedValues: ['Enabled', 'Disabled']
        });

        const trafficCaptureReplayerParam = new CfnParameter(this, "TrafficCaptureReplayer", {
            description: "Traffic capture and replayer is enabled in the Migration Console",
            default: 'Disabled',
            allowedValues: ['Enabled', 'Disabled']
        });

        const reindexFromSnapshotEnabledCondition = new CfnCondition(this, 'ReindexFromSnapshotEnabledCondition', {
            expression: Fn.conditionEquals(reindexFromSnapshotParam.valueAsString, 'Enabled'),
        });
        const trafficReplayerEnabledCondition = new CfnCondition(this, 'TrafficReplayerEnabledCondition', {
            expression: Fn.conditionEquals(trafficCaptureReplayerParam.valueAsString, 'Enabled'),
        });

        const fileContent = Fn.join('', [
            '{\n',
            '  "migration": {\n',
            '    "stage": "', stageParameter.valueAsString, '",\n',
            '    "vpcId": "', vpc.vpcId, ',\n',
            '    "reindexFromSnapshotServiceEnabled": ', Fn.conditionIf(reindexFromSnapshotEnabledCondition.logicalId, 'true', 'false').toString(), ',\n',
            '    "trafficReplayerServiceEnabled": ', Fn.conditionIf(trafficReplayerEnabledCondition.logicalId, 'true', 'false').toString(), '\n',
            '  }\n',
            '}',
        ]);

        const solutionsUserAgent = `AwsSolution/${props.solutionId}/${props.solutionVersion}`
        const cfnInitConfig: InitElement[] = [
            InitCommand.shellCommand(`echo "export MIGRATIONS_APP_REGISTRY_ARN=${appRegistryAppARN}; export MIGRATIONS_USER_AGENT=${solutionsUserAgent}" > /etc/profile.d/solutionsEnv.sh`),
            InitFile.fromFileInline("/opensearch-migrations/initBootstrap.sh", './initBootstrap.sh', {
                mode: "000744"
            }),
            InitCommand.shellCommand("sudo -s /bin/bash /opensearch-migrations/initBootstrap.sh"),
            InitFile.fromString('/opensearch-migrations/cdk.context.json', fileContent) /** TODO: Fix order of operations to import this file directly */
        ]

        const bootstrapRole = new Role(this, 'BootstrapRole', {
            assumedBy: new ServicePrincipal('ec2.amazonaws.com'),
            description: 'EC2 Bootstrap Role'
        });
        bootstrapRole.addManagedPolicy(ManagedPolicy.fromAwsManagedPolicyName('AdministratorAccess'))

        new InstanceProfile(this, 'BootstrapInstanceProfile', {
            instanceProfileName: `bootstrap-${stageParameter.valueAsString}-instance-profile`,
            role: bootstrapRole
        })

        const hasher = createHash('md5');
        this.node.findAll()
            .filter((c: any) => c instanceof CfnParameter)
            .map((c: any) => c as CfnParameter)
            .forEach((c: CfnParameter) => {
                let strValue;
                try {
                    strValue = c.valueAsString;
                } catch {
                    strValue = c.valueAsList.join(",");
                }

                hasher.update(strValue);
            });

        new Instance(this, 'BootstrapEC2Instance', {
            vpc: vpc,
            instanceName: `bootstrap-${stageParameter.valueAsString}-instance-${hasher.digest('base64')}`,
            instanceType: InstanceType.of(InstanceClass.T3, InstanceSize.LARGE),
            machineImage: MachineImage.latestAmazonLinux2023(),
            role: bootstrapRole,
            blockDevices: [
                {
                    deviceName: "/dev/xvda",
                    volume: BlockDeviceVolume.ebs(50)
                }
            ],
            init: CloudFormationInit.fromElements(...cfnInitConfig),
            initOptions: {
                printLog: true,
                ignoreFailures: true,
            },
        });

        const dynamicEc2ImageParameter = this.node.findAll()
            .filter(c => c instanceof CfnParameter)
            .filter(c => (c as CfnParameter).type === "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>")
            .pop() as CfnParameter;
        if (dynamicEc2ImageParameter) {
            dynamicEc2ImageParameter.description = "Latest Amazon Linux Image Id for the build machine"
            dynamicEc2ImageParameter.overrideLogicalId("LastedAmazonLinuxImageId");
        }

        const parameterGroups = [];

        parameterGroups.push({
            Label: { default: "Migration Assistant Features" },
            Parameters: [reindexFromSnapshotParam.logicalId, trafficCaptureReplayerParam.logicalId]
        });

        if (!props.useExistingVpc) {
            parameterGroups.push({
                Label: { default: "Network Options" },
                Parameters: ['VpcId', 'SubnetIds', 'AvailabilityZones'],
            });
        }
        parameterGroups.push({
            Label: { default: "Additional parameters" },
            Parameters: [stageParameter.logicalId]
        });
        parameterGroups.push({
            Label: { default: "System parameters" },
            Parameters: [dynamicEc2ImageParameter?.logicalId]
        });

        this.templateOptions.metadata = {
            'AWS::CloudFormation::Interface': {
                ParameterGroups: parameterGroups
            }
        }
    }
}