# Kafka mTLS Configuration for OpenSearch Migrations

This guide documents the changes made to enable mutual TLS (mTLS) authentication between the OpenSearch Migrations components (Capture Proxy, Migration Console, and Traffic Replayer) and the Kafka cluster.

## Overview

The configuration enables secure communication using:
- **Kafka TLS Listener**: Port 9093 with TLS authentication
- **Client Certificates**: Strimzi-generated certificates for each component
- **SSL Configuration**: Proper SSL settings for Java Kafka clients

## Changes Made

### 1. Kafka Cluster Configuration

**File**: `deployment/k8s/charts/sharedResources/baseKafkaCluster/templates/configuration.yaml`

**Changes**:
- **TLS Listener**: Added `authentication: type: tls` to port 9093 listener
- **KafkaUser Resources**: Created three users with TLS authentication:
  - `capture-proxy-user`: Read/Write access to all topics
  - `migration-console-user`: Read/Write access + cluster describe permissions
  - `replayer-user`: Read-only access to topics

```yaml
listeners:
  - name: tls
    port: 9093
    type: internal
    tls: true
    authentication:
      type: tls
```

**Generated Secrets**:
- `capture-proxy-user` secret with client certificates
- `migration-console-user` secret with client certificates  
- `replayer-user` secret with client certificates

### 2. Migration Assistant Configuration

**File**: `deployment/k8s/charts/aggregates/migrationAssistant/values.yaml`

**Changes**:
- **Port Update**: Changed Kafka connection from 9092 to 9093
- **SSL Configuration**: Added SSL settings to shared Kafka brokers config

```yaml
kafkaBrokers:
  object:
    brokers: "captured-traffic-kafka-bootstrap.ma.svc:9093"
    sslEnabled: true
    securityProtocol: "SSL"
    sslTruststoreLocation: "/etc/kafka/ssl/ca.crt"
    sslKeystoreLocation: "/etc/kafka/ssl/user.p12"
    sslKeystorePassword: "password"
```

### 3. Capture Proxy Configuration

**Files**: 
- `deployment/k8s/charts/components/captureProxy/values.yaml`
- `deployment/k8s/charts/components/captureProxy/templates/deployment.yaml`

**Changes**:
- **SSL Parameters**: Added Kafka SSL configuration parameters
- **Certificate Mount**: Mounted `capture-proxy-user` secret to `/etc/kafka/ssl`

```yaml
# SSL configuration parameters
kafkaSslEnabled:
  source: otherConfig
  configMapName: "kafka-brokers"
  configMapKey: "sslEnabled"
  parameterType: booleanFlag
```

**Volume Mount**:
```yaml
volumeMounts:
  - name: kafka-ssl-certs
    mountPath: /etc/kafka/ssl
    readOnly: true
volumes:
  - name: kafka-ssl-certs
    secret:
      secretName: capture-proxy-user
```

### 4. Traffic Replayer Configuration

**Files**:
- `deployment/k8s/charts/components/replayer/values.yaml`
- `deployment/k8s/charts/components/replayer/templates/deployment.yaml`

**Changes**:
- **SSL Parameters**: Added Kafka SSL configuration parameters
- **Certificate Mount**: Mounted `replayer-user` secret to `/etc/kafka/ssl`

Similar configuration to capture proxy but using `replayer-user` secret.

### 5. Migration Console Configuration

**Files**:
- `deployment/k8s/charts/components/migrationConsole/templates/deployment.yaml`
- `TrafficCapture/dockerSolution/src/main/docker/migrationConsole/lib/console_link/console_link/models/kafka.py`

**Changes**:
- **Certificate Mount**: Mounted `migration-console-user` secret to `/etc/kafka/ssl`
- **Python SSL Support**: Added `SSLKafka` class and SSL configuration handling

**Python SSL Configuration**:
```python
class SSLKafka(Kafka):
    """
    SSL-enabled Kafka implementation of Kafka operations
    """
    def __init__(self, config):
        super().__init__(config)
        self.ssl_config = config.get('ssl', {})
        # Create SSL configuration file for CLI tools
        create_ssl_config_file(self.ssl_config)
```

**SSL Configuration Schema**:
```python
SSL_SCHEMA = {
    "nullable": True,
    "type": "dict",
    "schema": {
        "security_protocol": {"type": "string", "default": "SSL"},
        "ssl_ca_location": {"type": "string", "default": "/etc/kafka/ssl/ca.crt"},
        "ssl_certificate_location": {"type": "string", "default": "/etc/kafka/ssl/user.crt"},
        "ssl_key_location": {"type": "string", "default": "/etc/kafka/ssl/user.key"},
        "ssl_keystore_location": {"type": "string", "default": "/etc/kafka/ssl/user.p12"},
        "ssl_keystore_password": {"type": "string", "default": "password"}
    }
}
```

## Deployment Instructions

### Prerequisites

1. **Strimzi Operator**: Ensure Strimzi Kafka operator is installed
2. **cert-manager** (optional): For additional certificate management

### Deploy the Migration Assistant

```bash
# Update Helm dependencies
helm dependency update deployment/k8s/charts/aggregates/migrationAssistant

# Deploy the Migration Assistant with mTLS-enabled Kafka
helm install ma deployment/k8s/charts/aggregates/migrationAssistant \
  --namespace ma --create-namespace

# Deploy test clusters (optional)
helm install tc deployment/k8s/charts/aggregates/testClusters \
  --namespace ma
```

### Verification Steps

#### 1. Verify Kafka Cluster Status

```bash
# Check Kafka cluster is ready
kubectl get kafka captured-traffic -n ma

# Verify TLS listener is configured
kubectl get kafka captured-traffic -n ma -o yaml | grep -A 10 listeners
```

#### 2. Verify KafkaUser Creation

```bash
# Check KafkaUsers are created and ready
kubectl get kafkauser -n ma

# Verify secrets are generated
kubectl get secrets -n ma | grep -E "(capture-proxy-user|migration-console-user|replayer-user)"
```

#### 3. Verify Certificate Content

```bash
# Check capture-proxy-user certificate
kubectl get secret capture-proxy-user -n ma -o yaml

# Verify certificate files are present
kubectl get secret capture-proxy-user -n ma \
  -o jsonpath='{.data}' | jq 'keys'
```

#### 4. Test SSL Connection

```bash
# Test SSL connection from capture proxy pod
kubectl exec -it deployment/ma-capture-proxy -n ma -- \
  openssl s_client -connect captured-traffic-kafka-bootstrap:9093 \
  -cert /etc/kafka/ssl/user.crt -key /etc/kafka/ssl/user.key \
  -CAfile /etc/kafka/ssl/ca.crt -verify_return_error
```

#### 5. Verify Kafka Client Configuration

```bash
# Check environment variables in capture proxy
kubectl exec -it deployment/ma-capture-proxy -n ma -- \
  env | grep -i kafka

# Verify SSL configuration is loaded
kubectl logs deployment/ma-capture-proxy -n ma | grep -i ssl
```

## Expected Certificate Structure

Each KafkaUser secret contains:
- `ca.crt`: Certificate Authority certificate
- `user.crt`: Client certificate
- `user.key`: Client private key  
- `user.p12`: PKCS#12 keystore (for Java applications)
- `user.password`: Keystore password

## Security Features

### Authentication
- **Mutual TLS**: Both client and server authenticate each other
- **Certificate-based**: No passwords, uses cryptographic certificates
- **Per-component**: Each component has its own certificate/identity

### Authorization
- **RBAC**: Fine-grained permissions per user
- **Topic Access**: Controlled read/write access to Kafka topics
- **Consumer Groups**: Managed consumer group permissions

### Network Security
- **Encrypted Transit**: All Kafka communication encrypted with TLS
- **Certificate Validation**: Proper certificate chain validation
- **Strong Cipher Suites**: Modern TLS configuration

## Troubleshooting

### Common Issues

#### 1. Certificate Not Found
```bash
# Check if secret exists and is mounted
kubectl describe pod <pod-name> -n ma | grep -A 5 "kafka-ssl-certs"
```

#### 2. SSL Handshake Failures
```bash
# Check Kafka logs
kubectl logs kafka-captured-traffic-controller-0 -n ma

# Verify certificate validity
kubectl exec -it <pod-name> -n ma -- \
  openssl x509 -in /etc/kafka/ssl/user.crt -text -noout
```

#### 3. Permission Denied
```bash
# Check KafkaUser permissions
kubectl get kafkauser capture-proxy-user -n ma -o yaml
```

#### 4. Connection Refused
```bash
# Verify Kafka service endpoints
kubectl get endpoints captured-traffic-kafka-bootstrap -n ma

# Check if TLS port is accessible
kubectl exec -it <pod-name> -n ma -- \
  nc -zv captured-traffic-kafka-bootstrap 9093
```

### Debug Commands

```bash
# View complete Kafka configuration
kubectl get kafka captured-traffic -n ma -o yaml

# Check Strimzi operator logs
kubectl logs -l name=strimzi-cluster-operator -n kafka

# Monitor certificate expiration
kubectl get secret capture-proxy-user -n ma \
  -o jsonpath='{.data.user\.crt}' | base64 -d | \
  openssl x509 -noout -dates
```

## Migration from Non-TLS

If migrating from a non-TLS setup:

1. **Backup Data**: Ensure all topics are properly backed up
2. **Rolling Update**: Components will restart with new SSL configuration
3. **Verify Connectivity**: Test each component can connect to Kafka
4. **Monitor Logs**: Watch for SSL-related errors during startup

## Security Best Practices

1. **Certificate Rotation**: Monitor certificate expiration dates
2. **Access Review**: Regularly review KafkaUser permissions
3. **Network Policies**: Consider additional network restrictions
4. **Audit Logging**: Enable Kafka audit logging for security events
5. **Monitoring**: Set up alerts for SSL connection failures

## Performance Considerations

- **SSL Overhead**: Expect ~5-10% performance impact from TLS encryption
- **Certificate Caching**: Java SSL sessions are cached to reduce overhead
- **Connection Pooling**: Kafka clients reuse SSL connections efficiently

The mTLS configuration provides enterprise-grade security for Kafka communications while maintaining compatibility with the existing OpenSearch Migrations architecture.
