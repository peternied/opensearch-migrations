// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: Apache-2.0

import { Aws, CfnCondition, CfnMapping, CfnParameter, CustomResource, Fn, Stack, StackProps, Tags } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import {
    BlockDeviceVolume,
    CloudFormationInit,
    ISubnet,
    IVpc,
    InitCommand,
    InitElement,
    InitFile,
    Instance,
    InstanceClass,
    InstanceSize,
    InstanceType,
    IpAddresses,
    MachineImage,
    Subnet,
    SubnetType,
    Vpc
} from "aws-cdk-lib/aws-ec2";
import { InstanceProfile, ManagedPolicy, PolicyStatement, Role, ServicePrincipal } from "aws-cdk-lib/aws-iam";
import { CfnDocument } from "aws-cdk-lib/aws-ssm";
import { Application, AttributeGroup } from "@aws-cdk/aws-servicecatalogappregistry-alpha";
import { Code, Function, Runtime } from "aws-cdk-lib/aws-lambda";
import * as crypto from 'crypto';

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
            stage // If your solution supports multiple deployments in the same region, add stage to the application name to make it unique.
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

        // CFN template format version
        this.templateOptions.templateFormatVersion = '2010-09-09';

        // CFN Mappings
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


        let vpc = undefined;

        if (props.useExistingVpc) {
            // Parameters for VPC details
            // const vpcIdParam = new CfnParameter(this, 'VpcId', {
            //     type: 'AWS::EC2::VPC::Id',
            //     default: 'abc',
            //     description: 'The ID of the existing VPC',
            // });

            // const subnetIdsParam = new CfnParameter(this, 'SubnetIds', {
            //     type: 'List<AWS::EC2::Subnet::Id>',
            //     default: 'abc',
            //     description: 'List of subnet IDs in the VPC',
            // });

            // const availabilityZonesParam = new CfnParameter(this, 'AvailabilityZones', {
            //     type: 'List<String>',
            //     default: 'abc',
            //     description: 'List of availability zones for the subnets',
            // });

            // Import the VPC
            // vpc = Vpc.fromVpcAttributes(this, 'ImportedVPC', {
            //     vpcId: vpcIdParam.valueAsString,
            //     availabilityZones: this.availabilityZones
            // });

        }

        vpc = new Vpc(this, 'Vpc', {
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

        var reindexFromSnapshotParam = new CfnParameter(this, "ReindexFromSnapshot", {
            description: "If the backfill via reindex from snapshot should be enabled in the Migration Console",
            default: 'Enabled',
            allowedValues: ['Enabled', 'Disabled']
        });

        var trafficCaptureReplayerParam = new CfnParameter(this, "TrafficCaptureReplayer", {
            description: "If the traffic capture and replayer should be enabled in the Migration Console",
            default: 'Disabled',
            allowedValues: ['Enabled', 'Disabled']
        });

        const reindexFromSnapshotEnabledCondition = new CfnCondition(this, 'ReindexFromSnapshotEnabledCondition', {
            expression: Fn.conditionEquals(reindexFromSnapshotParam.valueAsString, 'Enabled'),
        });

        const trafficReplayerEnabledCondition = new CfnCondition(this, 'TrafficReplayerEnabledCondition', {
            expression: Fn.conditionEquals(trafficCaptureReplayerParam.valueAsString, 'Enabled'),
        });

        // Step 3: Construct the File Content
        const fileContent = Fn.join('', [
            '{\n',
            '  "migration": {\n',
            '    "stage": ', stageParameter.valueAsString, ',\n',
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
            InitFile.fromString('/opensearch-migrations/cdk.context.json', fileContent)
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

        var hasher = crypto.createHash('md5');
        this.node.findAll()
        .filter(c => c instanceof CfnParameter)
        .forEach(c => {
            hasher.update((c as CfnParameter).valueAsString);
        });

        const buildMachine = new Instance(this, 'BootstrapEC2Instance', {
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
            userDataCausesReplacement: true,
        });

        var dynamicEc2ImageParameter = this.node.findAll()
            .filter(c => c instanceof CfnParameter)
            .filter(c => (c as CfnParameter).type === "AWS::SSM::Parameter::Value<AWS::EC2::Image::Id>")
            .pop() as CfnParameter;
        if (dynamicEc2ImageParameter) {
            dynamicEc2ImageParameter.description = "Latest Amazon Linux Image Id for the build machine"
            dynamicEc2ImageParameter.overrideLogicalId("LastedAmazonLinuxImageId");
        }

        this.templateOptions.metadata = {
            'AWS::CloudFormation::Interface': {
                ParameterGroups: [
                    {
                        Label: { default: "Features" },
                        Parameters: [reindexFromSnapshotParam.logicalId, trafficCaptureReplayerParam.logicalId]
                    },
                    {
                        Label: { default: "Network Options" },
                        Parameters: ['VpcId', 'SubnetIds', 'AvailabilityZones'],
                    },
                    {
                        Label: { default: "Additional parameter" },
                        Parameters: [dynamicEc2ImageParameter?.logicalId]
                    }
                ]
            }
        }


    }
}