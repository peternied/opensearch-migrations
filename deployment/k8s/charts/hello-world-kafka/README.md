# Hello-World Kafka Helm Chart

This Helm chart deploys a simple "hello-world" application that includes:
1. A Kafka cluster using the Strimzi operator
2. A default Kafka topic
3. An admin container with Kubernetes tools installed for managing Kafka topics

## Prerequisites

- Kubernetes cluster
- Helm 3.x installed
- kubectl installed and configured to access your cluster

## Installation

There are two ways to install this chart depending on whether you already have the Strimzi Kafka Operator installed in your cluster:

### Option 1: If Strimzi is NOT already installed

1. Edit the `Chart.yaml` file and uncomment the dependencies section:

```yaml
dependencies:
  - name: strimzi-kafka-operator
    version: 0.43.0
    repository: "https://strimzi.io/charts/"
```

2. Update the Helm dependencies and install the chart:

```bash
# Create the kafka-demo namespace
kubectl create namespace kafka-demo

# Update the Helm dependencies
helm dependency update ./hello-world-kafka

# Install the chart in the kafka-demo namespace
helm install hello-kafka ./hello-world-kafka -n kafka-demo
```

### Option 2: If Strimzi IS already installed

If you already have Strimzi installed in your cluster, make sure the dependencies section in `Chart.yaml` remains commented out to avoid conflicts:

```bash
# Create the kafka-demo namespace if it doesn't exist
kubectl create namespace kafka-demo

# Install the chart in the kafka-demo namespace
helm install hello-kafka ./hello-world-kafka -n kafka-demo
```

## Configuration Options

The following table lists the configurable parameters of the hello-world-kafka chart:

| Parameter                          | Description                                     | Default           |
|-----------------------------------|-------------------------------------------------|-------------------|
| `kafka.clusterName`                | Name of the Kafka cluster                       | `hello-kafka`     |
| `kafka.replicas`                   | Number of Kafka nodes                           | `1`               |
| `kafka.storageType`                | Storage type (ephemeral or persistent-claim)    | `ephemeral`       |
| `kafka.storageSize`                | Size of storage                                 | `10Gi`            |
| `kafka.storageDeleteClaim`         | Whether to delete PVCs when uninstalling        | `true`            |
| `topic.name`                       | Default topic name                              | `hello-topic`     |
| `topic.partitions`                 | Number of partitions for the default topic      | `1`               |
| `topic.replicationFactor`          | Replication factor for the default topic        | `1`               |
| `adminPod.enabled`                 | Whether to deploy the admin pod                 | `true`            |
| `adminPod.image`                   | Image for the admin container                   | `bitnami/kubectl:latest` |
| `adminPod.kafkaTools`              | Whether to install Kafka tools                  | `true`            |

## Usage

### Accessing the Admin Container

The admin container provides scripts for managing Kafka topics. To use it:

1. Connect to the admin container:

```bash
kubectl exec -it deployment/hello-kafka-kafka-admin -n kafka-demo -- bash
```

2. Use the provided scripts to manage topics:

```bash
# Create a topic with 3 partitions and replication factor 1
/scripts/create-topic.sh my-new-topic 3 1

# List all topics
/scripts/list-topics.sh

# Delete a topic
/scripts/delete-topic.sh my-new-topic
```

### Accessing Kafka

The Kafka cluster is exposed internally within the Kubernetes cluster:

- Plain protocol: `hello-kafka:9092`
- TLS protocol: `hello-kafka:9093` (requires certificates)

## Uninstallation

```bash
# Uninstall the helm chart
helm uninstall hello-kafka -n kafka-demo

# Optionally delete the namespace
kubectl delete namespace kafka-demo
```

## Advanced Configuration

### Installing with Custom Values

You can customize the deployment by creating your own values file and using it during installation:

```bash
# Create a custom-values.yaml file with your specific configurations
cat > custom-values.yaml <<EOF
kafka:
  clusterName: "my-kafka"
  replicas: 3
  storageType: "persistent-claim"
  storageSize: "50Gi"
topic:
  name: "custom-topic"
  partitions: 3
  replicationFactor: 3
EOF

# Install the chart with custom values
helm install hello-kafka ./hello-world-kafka -n kafka-demo -f custom-values.yaml
```

### Dedicated Controller Setup

For production environments, you might want to use dedicated controller nodes:

```bash
# Create a production-values.yaml file
cat > production-values.yaml <<EOF
kafka:
  clusterName: "prod-kafka"
  replicas: 3
  storageType: "persistent-claim"
  storageSize: "50Gi"
  dedicatedController:
    replicas: 3
    storageSize: "20Gi"
EOF

# Install with production values
helm install hello-kafka ./hello-world-kafka -n kafka-demo -f production-values.yaml
```

### Custom Topic Configuration

```bash
# Create a topic-values.yaml file
cat > topic-values.yaml <<EOF
topic:
  name: "custom-topic"
  partitions: 3
  replicationFactor: 3
  configs:
    retention.ms: 604800000  # 7 days
    segment.bytes: 1073741824  # 1GB
EOF

# Install with custom topic configuration
helm install hello-kafka ./hello-world-kafka -n kafka-demo -f topic-values.yaml
