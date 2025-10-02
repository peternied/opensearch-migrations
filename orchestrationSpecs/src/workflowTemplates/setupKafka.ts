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

    .addTemplate("exportClusterCa", t => t
        .addRequiredInput("kafkaName", typeToken<string>())
        .addScriptTask(b => b
            .setImage("bitnami/kubectl:1.30")
            .setCommand(["bash", "-lc"])
            .setSource(`
                set -euo pipefail
                SECRET="{{inputs.parameters.kafkaName}}-cluster-ca-cert"
                # Extract PEM (base64-decoded) into a file for Argo to capture as a parameter.
                kubectl get secret "${SECRET}" -o jsonpath='{.data.ca\\.crt}' \\
                | base64 -d > /tmp/ca.crt
            `)
        )
        .addPathOutput("clusterCaPem", "/tmp/ca.crt", typeToken<string>())
    )

    .addTemplate("createKafkaPropertiesFile", t => t
        .addRequiredInput("secretName", typeToken<string>())
        .addRequiredInput("userSecretName", typeToken<string>())
        .addRequiredInput("caSecretName", typeToken<string>())
        .addRequiredInput("bootstrapServers", typeToken<string>())
        .addRequiredInput("clientId", typeToken<string>())
        .addOptionalInput("mountPath", s => "/opt/kafka-config")
        .addOptionalInput("targetNamespace", s => "{{workflow.namespace}}")
        .addScriptTask(b => b
            .setImage("bitnami/kubectl:1.30")
            .setCommand(["/bin/bash", "-euo", "pipefail", "-c"])
            .addEnv("SASL_USERNAME", {
                valueFrom: {
                    secretKeyRef: {
                        name: "{{inputs.parameters.userSecretName}}",
                        key: "username"
                    }
                }
            })
            .addEnv("SASL_PASSWORD", {
                valueFrom: {
                    secretKeyRef: {
                        name: "{{inputs.parameters.userSecretName}}",
                        key: "password"
                    }
                }
            })
            .addEnv("TRUSTPASS", {
                valueFrom: {
                    secretKeyRef: {
                        name: "{{inputs.parameters.caSecretName}}",
                        key: "ca.password"
                    }
                }
            })
            .setSource(`
                WORK=/work
                mkdir -p "$WORK"

                # Copy truststore from the mounted CA secret so we can package it into the new Secret
                cp /var/run/ca-secret/ca.p12 "$WORK/ca.p12"
                printf "%s" "$TRUSTPASS" > "$WORK/ca.password"

                # Render kafka.properties using ENV vars
                KAFKA_PROPERTIES_FILE="$WORK/kafka.properties"
                cat > "$KAFKA_PROPERTIES_FILE" <<EOF
security.protocol=SASL_SSL
sasl.mechanism=SCRAM-SHA-512
sasl.jaas.config=org.apache.kafka.common.security.scram.ScramLoginModule required username='\${SASL_USERNAME}' password='\${SASL_PASSWORD}';
ssl.truststore.type=PKCS12
ssl.truststore.location={{inputs.parameters.mountPath}}/ca.p12
ssl.truststore.password=\${TRUSTPASS}
bootstrap.servers={{inputs.parameters.bootstrapServers}}
\$( [[ -n "{{inputs.parameters.clientId}}" ]] && echo "client.id={{inputs.parameters.clientId}}" )
EOF

                kubectl -n "{{inputs.parameters.targetNamespace}}" create secret generic "{{inputs.parameters.secretName}}" \\
                  --from-file=kafka.properties="$KAFKA_PROPERTIES_FILE" \\
                  --from-file=ca.p12="$WORK/ca.p12" \\
                  --from-file=ca.password="$WORK/ca.password" \\
                  --dry-run=client -o yaml | kubectl apply -f -
            `)
            .setPodSpecPatch(`
                {
                    "volumes": [
                        {
                            "name": "ca-secret",
                            "secret": {
                                "secretName": "{{inputs.parameters.caSecretName}}",
                                "items": [
                                    {"key": "ca.p12", "path": "ca.p12"}
                                ]
                            }
                        },
                        { "name": "work", "emptyDir": {} }
                    ],
                    "containers": [
                        {
                            "name": "main",
                            "volumeMounts": [
                                {"name": "ca-secret", "mountPath": "/var/run/ca-secret", "readOnly": true},
                                {"name": "work", "mountPath": "/work"}
                            ]
                        }
                    ],
                    "serviceAccountName": "argo-workflow-executor"
                }
            `)
        )
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
            .addTask("exportClusterCa", INTERNAL, "exportClusterCa", c =>
                c.register({kafkaName: b.inputs.kafkaName}),
                {dependencies: ["deployCluster"]})
            .addTask("createCaptureProxyProperties", INTERNAL, "createKafkaPropertiesFile", c =>
                c.register({
                    secretName: expr.concat(b.inputs.kafkaName, expr.literal("-capture-proxy-properties")),
                    userSecretName: c.tasks.createUsers.outputs.captureProxySecret,
                    caSecretName: expr.concat(b.inputs.kafkaName, expr.literal("-cluster-ca-cert")),
                    bootstrapServers: c.tasks.deployCluster.outputs.bootstrapServers,
                    clientId: expr.concat(b.inputs.kafkaName, expr.literal("-capture-proxy"))
                }),
                {dependencies: ["createUsers"]})
            .addTask("createReplayerProperties", INTERNAL, "createKafkaPropertiesFile", c =>
                c.register({
                    secretName: expr.concat(b.inputs.kafkaName, expr.literal("-replayer-properties")),
                    userSecretName: c.tasks.createUsers.outputs.replayerSecret,
                    caSecretName: expr.concat(b.inputs.kafkaName, expr.literal("-cluster-ca-cert")),
                    bootstrapServers: c.tasks.deployCluster.outputs.bootstrapServers,
                    clientId: expr.concat(b.inputs.kafkaName, expr.literal("-replayer"))
                }),
                {dependencies: ["createUsers"]})
            .addTask("createConsoleProperties", INTERNAL, "createKafkaPropertiesFile", c =>
                c.register({
                    secretName: expr.concat(b.inputs.kafkaName, expr.literal("-console-properties")),
                    userSecretName: c.tasks.createUsers.outputs.consoleSecret,
                    caSecretName: expr.concat(b.inputs.kafkaName, expr.literal("-cluster-ca-cert")),
                    bootstrapServers: c.tasks.deployCluster.outputs.bootstrapServers,
                    clientId: expr.concat(b.inputs.kafkaName, expr.literal("-console"))
                }),
                {dependencies: ["createUsers"]})
        )
        .addExpressionOutput("kafkaName", c => c.inputs.kafkaName)
        .addExpressionOutput("bootstrapServers", c => c.tasks.deployCluster.outputs.bootstrapServers)
        .addExpressionOutput("clusterCaPem", c => c.tasks.exportClusterCa.outputs.clusterCaPem)
        .addExpressionOutput("captureProxyPropertiesSecret", c => expr.concat(c.inputs.kafkaName, expr.literal("-capture-proxy-properties")))
        .addExpressionOutput("replayerPropertiesSecret", c => expr.concat(c.inputs.kafkaName, expr.literal("-replayer-properties")))
        .addExpressionOutput("consolePropertiesSecret", c => expr.concat(c.inputs.kafkaName, expr.literal("-console-properties")))
    )

    .getFullScope();
