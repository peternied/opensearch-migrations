import {WorkflowBuilder} from "@/argoWorkflowBuilders/models/workflowBuilder";
import {CommonWorkflowParameters} from "@/workflowTemplates/commonWorkflowTemplates";
import {INTERNAL} from "@/argoWorkflowBuilders/models/taskBuilder";
import {BaseExpression, expr} from "@/argoWorkflowBuilders/models/expression";
import {selectInputsForRegister} from "@/argoWorkflowBuilders/models/parameterConversions";
import {typeToken} from "@/argoWorkflowBuilders/models/sharedTypes";


function makeDeployKafkaClusterZookeeperManifest(kafkaName: BaseExpression<string>) {
    return {
        apiVersion: "kafka.strimzi.io/v1beta2",
        kind: "Kafka",
        metadata: {
            name: kafkaName
        },
        spec: {
            kafka: {
                version: "3.9.0",
                replicas: 1,
                listeners: [
                    {
                        name: "tls",
                        port: 9093,
                        type: "internal",
                        tls: true,
                        authentication: {
                            type: "tls"
                        }
                    }
                ],
                config: {
                    "offsets.topic.replication.factor": 1,
                    "transaction.state.log.replication.factor": 1,
                    "transaction.state.log.min.isr": 1,
                    "default.replication.factor": 1,
                    "min.insync.replicas": 1,
                    "inter.broker.protocol.version": "3.9"
                },
                storage: {
                    type: "ephemeral"
                }
            },
            zookeeper: {
                replicas: 3,
                storage: {
                    type: "ephemeral"
                }
            },
            entityOperator: {
                topicOperator: {},
                userOperator: {}
            }
        }
    };
}

function makeDeployKafkaClusterKraftManifest(kafkaName: BaseExpression<string>) {
    return {
        apiVersion: "kafka.strimzi.io/v1beta2",
        kind: "Kafka",
        metadata: {
            name: kafkaName,
            annotations: {
                "strimzi.io/node-pools": "enabled",
                "strimzi.io/kraft": "enabled"
            }
        },
        spec: {
            kafka: {
                version: "3.9.0",
                metadataVersion: "3.9-IV0",
                readinessProbe: {
                    initialDelaySeconds: 1,
                    periodSeconds: 2,
                    timeoutSeconds: 2,
                    failureThreshold: 1
                },
                livenessProbe: {
                    initialDelaySeconds: 1,
                    periodSeconds: 2,
                    timeoutSeconds: 2,
                    failureThreshold: 2
                },
                listeners: [
                    {
                        name: "tls",
                        port: 9093,
                        type: "internal",
                        tls: true,
                        authentication: {
                            type: "tls"
                        }
                    }
                ],
                config: {
                    "auto.create.topics.enable": false,
                    "offsets.topic.replication.factor": 1,
                    "transaction.state.log.replication.factor": 1,
                    "transaction.state.log.min.isr": 1,
                    "default.replication.factor": 1,
                    "min.insync.replicas": 1
                }
            },
            entityOperator: {
                topicOperator: {},
                userOperator: {}
            }
        }
    };
}

function makeDeployKafkaNodePool(kafkaName: BaseExpression<string>) {
    return {
        apiVersion: "kafka.strimzi.io/v1beta2",
        kind: "KafkaNodePool",
        metadata: {
            name: "dual-role",
            labels: {
                "strimzi.io/cluster": kafkaName
            }
        },
        spec: {
            replicas: 1,
            roles: [
                "controller",
                "broker"
            ],
            storage: {
                type: "jbod",
                volumes: [
                    {
                        id: 0,
                        type: "persistent-claim",
                        size: "5Gi",
                        deleteClaim: false,
                        kraftMetadata: "shared"
                    }
                ]
            }
        }
    };
}

function makeKafkaUserManifest(args: {
    kafkaName: BaseExpression<string>,
    userName: BaseExpression<string>,
    userType: BaseExpression<string>
}) {
    // Define ACLs based on user type
    const acls = [];
    
    // Common ACLs for all users - allow describe on all topics and groups
    acls.push(
        {
            operation: "Describe",
            resource: {
                type: "topic",
                name: "*",
                patternType: "literal"
            }
        },
        {
            operation: "Describe",
            resource: {
                type: "group",
                name: "*",
                patternType: "literal"
            }
        }
    );
    
    // Use toString() to compare BaseExpression to string
    const userType = args.userType.toString();
    
    // Add specific ACLs based on user type
    if (userType === "capture-proxy") {
        // Capture proxy needs to produce to topics
        acls.push(
            {
                operation: "Write",
                resource: {
                    type: "topic",
                    name: "*",
                    patternType: "literal"
                }
            },
            {
                operation: "Create",
                resource: {
                    type: "topic",
                    name: "*",
                    patternType: "literal"
                }
            }
        );
    } else if (userType === "replayer") {
        // Replayer needs to consume from topics
        acls.push(
            {
                operation: "Read",
                resource: {
                    type: "topic",
                    name: "*",
                    patternType: "literal"
                }
            },
            {
                operation: "Read",
                resource: {
                    type: "group",
                    name: "*",
                    patternType: "literal"
                }
            }
        );
    } else if (userType === "console") {
        // Console needs to read and write for management purposes
        acls.push(
            {
                operation: "Read",
                resource: {
                    type: "topic",
                    name: "*",
                    patternType: "literal"
                }
            },
            {
                operation: "Write",
                resource: {
                    type: "topic",
                    name: "*",
                    patternType: "literal"
                }
            },
            {
                operation: "Create",
                resource: {
                    type: "topic",
                    name: "*",
                    patternType: "literal"
                }
            },
            {
                operation: "Read",
                resource: {
                    type: "group",
                    name: "*",
                    patternType: "literal"
                }
            }
        );
    }
    
    return {
        apiVersion: "kafka.strimzi.io/v1beta2",
        kind: "KafkaUser",
        metadata: {
            name: args.userName,
            labels: {
                "strimzi.io/cluster": args.kafkaName
            }
        },
        spec: {
            authentication: {
                type: "tls"
            },
            authorization: {
                type: "simple",
                acls: acls
            }
        }
    };
}

function makeKafkaTopicManifest(args: {
    kafkaName: BaseExpression<string>,
    topicName: BaseExpression<string>,
    topicPartitions: BaseExpression<number>,
    topicReplicas: BaseExpression<number>
}) {
    return {
        apiVersion: "kafka.strimzi.io/v1beta2",
        kind: "KafkaTopic",
        metadata: {
            name: args.topicName,
            labels: {
                "strimzi.io/cluster": args.kafkaName,
            }
        },
        spec: {
            partitions: args.topicPartitions,
            replicas: args.topicReplicas,
            config: {
                "retention.ms": 604800000,
                "segment.bytes": 1073741824
            }
        }
    };
}


export const SetupKafka = WorkflowBuilder.create({
    k8sResourceName: "setup-kafka",
    serviceAccountName: "argo-workflow-executor",
    k8sMetadata: {},
    parallelism: 1
})
    .addParams(CommonWorkflowParameters)


    .addTemplate("deployKafkaClusterZookeeper", t => t
        .addRequiredInput("kafkaName", typeToken<string>())
        .addResourceTask(b => b
            .setDefinition({
                action: "create",
                setOwnerReference: true,
                successCondition: "status.listeners",
                manifest: makeDeployKafkaClusterZookeeperManifest(b.inputs.kafkaName)
            }))
        .addJsonPathOutput("brokers", "{.status.listeners[?(@.name=='tls')].bootstrapServers}",
            typeToken<string>())
    )


    .addTemplate("deployKafkaNodePool", t => t
        .addRequiredInput("kafkaName", typeToken<string>())
        .addResourceTask(b => b
            .setDefinition({
                action: "apply",
                setOwnerReference: true,
                manifest: makeDeployKafkaNodePool(b.inputs.kafkaName)
            }))
    )


    .addTemplate("deployKafkaClusterKraft", t => t
        .addRequiredInput("kafkaName", typeToken<string>())
        .addResourceTask(b => b
            .setDefinition({
                action: "apply",
                setOwnerReference: true,
                successCondition: "status.listeners",
                manifest: makeDeployKafkaClusterKraftManifest(b.inputs.kafkaName)
            }))
        .addJsonPathOutput("brokers", "{.status.listeners[?(@.name=='tls')].bootstrapServers}",
            typeToken<string>())
    )


    .addTemplate("clusterDeploy", t => t
        .addRequiredInput("kafkaName", typeToken<string>())
        .addOptionalInput("useKraft", s => true)
        .addDag(b => b
            .addTask("deployPool", INTERNAL, "deployKafkaNodePool", c =>
                    c.register({kafkaName: b.inputs.kafkaName}),
                {when: b.inputs.useKraft})
            .addTask("deployKafkaClusterKraft", INTERNAL, "deployKafkaClusterKraft", c =>
                    c.register(selectInputsForRegister(b, c)),
                {when: b.inputs.useKraft})
            .addTask("deployKafkaClusterZookeeper", INTERNAL, "deployKafkaClusterZookeeper", c =>
                    c.register(selectInputsForRegister(b, c)),
                {when: expr.not(b.inputs.useKraft)})
        )
        .addExpressionOutput("kafkaName", c => c.inputs.kafkaName)
        .addExpressionOutput("bootstrapServers", c =>
            expr.ternary(expr.equals(expr.literal("Skipped"), c.tasks.deployKafkaClusterKraft.status),
                c.tasks.deployKafkaClusterZookeeper.outputs.brokers,
                c.tasks.deployKafkaClusterKraft.outputs.brokers))
    )

    .addTemplate("createKafkaTopic", t => t
        .addRequiredInput("kafkaName", typeToken<string>())
        .addRequiredInput("topicName", typeToken<string>())
        .addRequiredInput("topicPartitions", typeToken<number>())
        .addRequiredInput("topicReplicas", typeToken<number>())

        .addResourceTask(b => b
            .setDefinition({
                action: "apply",
                setOwnerReference: true,
                successCondition: "status.topicName",
                manifest: makeKafkaTopicManifest(b.inputs)
            }))
        .addJsonPathOutput("topicName", "{.status.topicName}", typeToken<string>())
    )

    .addTemplate("createKafkaUser", t => t
        .addRequiredInput("kafkaName", typeToken<string>())
        .addRequiredInput("userName", typeToken<string>())
        .addRequiredInput("userType", typeToken<string>())
        
        .addResourceTask(b => b
            .setDefinition({
                action: "apply",
                setOwnerReference: true,
                successCondition: "status.username",
                manifest: makeKafkaUserManifest(b.inputs)
            }))
        .addJsonPathOutput("username", "{.status.username}", typeToken<string>())
        .addJsonPathOutput("secret", "{.status.secret}", typeToken<string>())
    )

    .addTemplate("createRequiredUsers", t => t
        .addRequiredInput("kafkaName", typeToken<string>())
        
        .addDag(b => b
            .addTask("createCaptureProxyUser", INTERNAL, "createKafkaUser", c =>
                c.register({
                    kafkaName: b.inputs.kafkaName,
                    userName: expr.concat(b.inputs.kafkaName, expr.literal("-capture-proxy")),
                    userType: expr.literal("capture-proxy")
                }))
            .addTask("createReplayerUser", INTERNAL, "createKafkaUser", c =>
                c.register({
                    kafkaName: b.inputs.kafkaName,
                    userName: expr.concat(b.inputs.kafkaName, expr.literal("-replayer")),
                    userType: expr.literal("replayer")
                }))
            .addTask("createConsoleUser", INTERNAL, "createKafkaUser", c =>
                c.register({
                    kafkaName: b.inputs.kafkaName,
                    userName: expr.concat(b.inputs.kafkaName, expr.literal("-console")),
                    userType: expr.literal("console")
                }))
        )
        .addExpressionOutput("captureProxyUsername", c => c.tasks.createCaptureProxyUser.outputs.username)
        .addExpressionOutput("replayerUsername", c => c.tasks.createReplayerUser.outputs.username)
        .addExpressionOutput("consoleUsername", c => c.tasks.createConsoleUser.outputs.username)
        .addExpressionOutput("captureProxySecret", c => c.tasks.createCaptureProxyUser.outputs.secret)
        .addExpressionOutput("replayerSecret", c => c.tasks.createReplayerUser.outputs.secret)
        .addExpressionOutput("consoleSecret", c => c.tasks.createConsoleUser.outputs.secret)
    )

    .addTemplate("setupKafkaWithUsers", t => t
        .addRequiredInput("kafkaName", typeToken<string>())
        .addOptionalInput("useKraft", s => true)
        
        .addDag(b => b
            .addTask("deployCluster", INTERNAL, "clusterDeploy", c =>
                c.register(selectInputsForRegister(b, c)))
            .addTask("createUsers", INTERNAL, "createRequiredUsers", c =>
                c.register({kafkaName: b.inputs.kafkaName}),
                {dependencies: ["deployCluster"]})
        )
        .addExpressionOutput("kafkaName", c => c.inputs.kafkaName)
        .addExpressionOutput("bootstrapServers", c => c.tasks.deployCluster.outputs.bootstrapServers)
        .addExpressionOutput("captureProxyUsername", c => c.tasks.createUsers.outputs.captureProxyUsername)
        .addExpressionOutput("replayerUsername", c => c.tasks.createUsers.outputs.replayerUsername)
        .addExpressionOutput("consoleUsername", c => c.tasks.createUsers.outputs.consoleUsername)
        .addExpressionOutput("captureProxySecret", c => c.tasks.createUsers.outputs.captureProxySecret)
        .addExpressionOutput("replayerSecret", c => c.tasks.createUsers.outputs.replayerSecret)
        .addExpressionOutput("consoleSecret", c => c.tasks.createUsers.outputs.consoleSecret)
    )

    .getFullScope();
