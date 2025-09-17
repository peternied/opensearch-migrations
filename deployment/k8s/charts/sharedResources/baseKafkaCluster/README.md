# Kafka TLS Configuration for OpenSearch Migrations

This directory contains resources for implementing TLS security for the Kafka cluster used by OpenSearch Migrations. The configuration sets up Strimzi Kafka with TLS authentication for secure communication between components.

## Prerequisites

Before deploying the OpenSearch Migrations with Kafka TLS support, you need to install the Strimzi Kafka Operator. The deployment will check for these CRDs and fail if they are not found.

### Installing Strimzi Kafka Operator

To install the Strimzi Kafka Operator, run the following command:

```bash
# Replace YOUR_NAMESPACE with the namespace where you're deploying the application
kubectl create -f "https://strimzi.io/install/latest?namespace=YOUR_NAMESPACE"
```

Verify the installation:

```bash
kubectl get pods -n YOUR_NAMESPACE -l name=strimzi-cluster-operator
```

You should see the Strimzi Cluster Operator pod running.

## Components Overview

The Kafka deployment consists of:

1. **Kafka Cluster**:
   - Uses KRaft mode (no ZooKeeper)
   - TLS-secured internal communication
   - Accessible via plain (non-TLS) and TLS protocols
   - Configurable storage type and size

2. **KafkaUsers**:
   - `capture-proxy-user`: For the capture proxy component
   - `migration-console-user`: For the migration console component
   - `replayer-user`: For the traffic replayer component
   - Each user has TLS authentication and appropriate ACLs

## Resource Dependencies

The OpenSearch Migrations components depend on secrets created by the Strimzi Operator:

- `capture-proxy-user`
- `migration-console-user`
- `replayer-user`

These secrets contain:
- `ca.crt`: CA certificate
- `user.crt`: User certificate
- `user.key`: User private key
- `user.p12`: PKCS#12 keystore

## Failsafe Mechanism

The deployment includes a failsafe mechanism to ensure components can start even if the Strimzi Operator hasn't created the user secrets yet:

1. Each component's init container will wait for the Kafka cluster to be ready
2. It will then wait for its corresponding user secret to be created (with a timeout)
3. If the timeout is reached, it will create a dummy secret with the required keys to allow the pod to start

## Troubleshooting

If you encounter issues with Kafka TLS:

1. Check if the Strimzi Operator is running:
   ```bash
   kubectl get pods -l name=strimzi-cluster-operator
   ```

2. Check the status of the Kafka cluster:
   ```bash
   kubectl get kafka -n YOUR_NAMESPACE
   kubectl describe kafka captured-traffic -n YOUR_NAMESPACE
   ```

3. Verify that the KafkaUser resources are created:
   ```bash
   kubectl get kafkausers -n YOUR_NAMESPACE
   ```

4. Check if the user secrets exist:
   ```bash
   kubectl get secret capture-proxy-user -n YOUR_NAMESPACE
   kubectl get secret migration-console-user -n YOUR_NAMESPACE
   kubectl get secret replayer-user -n YOUR_NAMESPACE
   ```

5. Check the logs of the init containers for more information:
   ```bash
   kubectl logs -n YOUR_NAMESPACE POD_NAME -c wait-for-kafka-and-secrets
   ```

## Disabling TLS (Not Recommended for Production)

For development or testing purposes, you can disable TLS by:

1. Removing the TLS listeners from the Kafka configuration
2. Removing the TLS authentication from the KafkaUser resources
3. Updating the component deployments to not mount the TLS secrets
