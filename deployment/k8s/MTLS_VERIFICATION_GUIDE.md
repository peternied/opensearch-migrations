# OpenSearch Migrations mTLS Verification Guide

This guide provides comprehensive instructions to verify mutual TLS (mTLS) configurations and functionality in the OpenSearch Migrations Kubernetes deployment.

## Prerequisites

- `kubectl` configured to access your Kubernetes cluster
- `openssl` for certificate verification
- `curl` with TLS support for testing HTTPS endpoints
- Access to the cluster where the migration assistant is deployed with mTLS enabled

## 1. Certificate Infrastructure Verification

### 1.1 cert-manager Status

```bash
# Check cert-manager installation
kubectl get pods -n cert-manager

# Verify cert-manager CRDs
kubectl get crd | grep cert-manager

# Check ClusterIssuer for internal certificates
kubectl get clusterissuer migration-ca-issuer -o yaml

# Verify CA certificate secret
kubectl get secret migration-ca-key-pair -n cert-manager -o yaml
```

**Expected Results:**
- cert-manager pods should be `Running`
- ClusterIssuer should be `Ready: True`
- CA secret should contain `tls.crt` and `tls.key`

### 1.2 Service Certificates

```bash
# List all certificates in migration namespace
kubectl get certificates -n ma

# Check certificate status
kubectl describe certificate -n ma

# Verify certificate secrets are created
kubectl get secrets -n ma | grep tls

# Check certificate expiration dates
for cert in $(kubectl get certificates -n ma -o name); do
  echo "=== $cert ==="
  kubectl get $cert -n ma -o jsonpath='{.status.notAfter}{"\n"}'
done
```

**Expected Results:**
- All certificates should have `Ready: True` status
- Certificate secrets should exist with `tls.crt` and `tls.key`
- Certificates should not be expired or near expiration

## 2. mTLS Configuration Verification

### 2.1 Capture Proxy mTLS Configuration

```bash
# Check Capture Proxy TLS configuration
kubectl get configmap capture-proxy-tls-config -n ma -o yaml

# Verify SSL config file is mounted
kubectl describe pod -l app=capture-proxy -n ma | grep -A 10 "Mounts:"

# Check TLS configuration in proxy settings
kubectl exec -it deployment/capture-proxy -n ma -- cat /usr/share/elasticsearch/config/proxy_tls.yml

# Verify service is using HTTPS port
kubectl get service capture-proxy -n ma -o yaml | grep -A 5 ports
```

### 2.2 Kafka mTLS Configuration

```bash
# Check Kafka SSL configuration
kubectl get configmap kafka-ssl-config -n ma -o yaml

# Verify Kafka SSL listeners
kubectl exec -it deployment/kafka -n ma -- cat /opt/kafka/config/server.properties | grep -E "(ssl|SSL)"

# Check if SSL port 9093 is listening
kubectl exec -it deployment/kafka -n ma -- netstat -tlnp | grep 9093

# Verify client SSL configuration
kubectl get configmap kafka-client-ssl-config -n ma -o yaml
```

### 2.3 Migration Console mTLS Configuration

```bash
# Check Migration Console HTTPS configuration
kubectl get configmap migration-console-tls-config -n ma -o yaml

# Verify TLS certificates are mounted
kubectl describe pod -l app=migration-console -n ma | grep -A 10 "Volumes:"

# Check if service is configured for HTTPS
kubectl get service migration-console -n ma -o yaml | grep -A 5 ports
```

## 3. Certificate Content Verification

### 3.1 Certificate Chain Validation

```bash
# Extract and verify capture proxy certificate
kubectl get secret capture-proxy-tls -n ma -o jsonpath='{.data.tls\.crt}' | base64 -d > /tmp/capture-proxy.crt
kubectl get secret migration-ca-key-pair -n cert-manager -o jsonpath='{.data.tls\.crt}' | base64 -d > /tmp/ca.crt

# Verify certificate chain
openssl verify -CAfile /tmp/ca.crt /tmp/capture-proxy.crt

# Check certificate details
openssl x509 -in /tmp/capture-proxy.crt -text -noout | grep -A 5 "Subject Alternative Name"

# Verify certificate contains correct DNS names
openssl x509 -in /tmp/capture-proxy.crt -text -noout | grep -E "(DNS:|Subject:)"
```

### 3.2 Certificate Expiration Check

```bash
#!/bin/bash
# Certificate expiration check script
NAMESPACE="ma"

echo "=== Certificate Expiration Check ==="
for secret in $(kubectl get secrets -n $NAMESPACE -o name | grep tls); do
  echo "Checking $secret..."
  kubectl get $secret -n $NAMESPACE -o jsonpath='{.data.tls\.crt}' | base64 -d | openssl x509 -noout -dates
  echo "---"
done
```

### 3.3 Certificate Subject and SAN Verification

```bash
# Check all service certificates have correct subjects
for service in capture-proxy kafka migration-console replayer; do
  echo "=== $service Certificate ==="
  kubectl get secret ${service}-tls -n ma -o jsonpath='{.data.tls\.crt}' | base64 -d | \
    openssl x509 -noout -text | grep -A 10 "Subject Alternative Name"
done
```

## 4. mTLS Handshake Verification

### 4.1 Service-to-Service mTLS Testing

```bash
# Test mTLS connection from Migration Console to Capture Proxy
kubectl exec -it deployment/migration-console -n ma -- \
  curl -v --cert /etc/ssl/certs/tls.crt --key /etc/ssl/private/tls.key \
  --cacert /etc/ssl/certs/ca.crt \
  https://capture-proxy:9200/_cluster/health

# Test mTLS connection to Kafka
kubectl exec -it deployment/capture-proxy -n ma -- \
  openssl s_client -connect kafka:9093 \
  -cert /etc/ssl/certs/tls.crt -key /etc/ssl/private/tls.key \
  -CAfile /etc/ssl/certs/ca.crt -verify_return_error
```

### 4.2 Certificate Verification in mTLS Handshake

```bash
# Test certificate verification with detailed output
kubectl exec -it deployment/migration-console -n ma -- \
  openssl s_client -connect capture-proxy:9200 \
  -cert /etc/ssl/certs/tls.crt -key /etc/ssl/private/tls.key \
  -CAfile /etc/ssl/certs/ca.crt -verify 3 -showcerts

# Verify peer certificate chain
kubectl exec -it deployment/capture-proxy -n ma -- \
  echo "GET /_cluster/health HTTP/1.1\nHost: capture-proxy\n\n" | \
  openssl s_client -connect kafka:9093 -cert /etc/ssl/certs/tls.crt \
  -key /etc/ssl/private/tls.key -CAfile /etc/ssl/certs/ca.crt -quiet
```

## 5. Application-Level mTLS Verification

### 5.1 Kafka mTLS Client Configuration

```bash
# Check Kafka client SSL properties
kubectl exec -it deployment/capture-proxy -n ma -- \
  cat /etc/kafka/ssl.properties

# Test Kafka producer with SSL
kubectl exec -it deployment/capture-proxy -n ma -- \
  kafka-console-producer.sh --bootstrap-server kafka:9093 \
  --producer.config /etc/kafka/ssl.properties \
  --topic test-ssl-topic

# Test Kafka consumer with SSL
kubectl exec -it deployment/replayer -n ma -- \
  kafka-console-consumer.sh --bootstrap-server kafka:9093 \
  --consumer.config /etc/kafka/ssl.properties \
  --topic logged-traffic --from-beginning --max-messages 1
```

### 5.2 HTTP Client mTLS Configuration

```bash
# Verify Migration Console can communicate with all services over mTLS
kubectl exec -it deployment/migration-console -n ma -- \
  curl --cert /etc/ssl/certs/tls.crt --key /etc/ssl/private/tls.key \
  --cacert /etc/ssl/certs/ca.crt \
  https://capture-proxy:9200/_cat/health

# Test Traffic Replayer mTLS connectivity
kubectl exec -it deployment/replayer -n ma -- \
  curl --cert /etc/ssl/certs/tls.crt --key /etc/ssl/private/tls.key \
  --cacert /etc/ssl/certs/ca.crt \
  https://migration-console:8443/api/status
```

## 6. External Cluster mTLS Verification

### 6.1 Source Cluster mTLS Connection

```bash
# Test mTLS connection to source cluster from Capture Proxy
kubectl exec -it deployment/capture-proxy -n ma -- \
  curl --cert /etc/ssl/certs/client.crt --key /etc/ssl/private/client.key \
  --cacert /etc/ssl/certs/source-ca.crt \
  https://elasticsearch-master:9200/_cluster/health

# Verify client certificate is accepted by source cluster
kubectl exec -it deployment/bulk-load -n ma -- \
  openssl s_client -connect elasticsearch-master:9200 \
  -cert /etc/ssl/certs/client.crt -key /etc/ssl/private/client.key \
  -CAfile /etc/ssl/certs/source-ca.crt -verify_return_error -servername elasticsearch-master
```

### 6.2 Target Cluster mTLS Connection

```bash
# Test mTLS connection to target cluster from Traffic Replayer
kubectl exec -it deployment/replayer -n ma -- \
  curl --cert /etc/ssl/certs/client.crt --key /etc/ssl/private/client.key \
  --cacert /etc/ssl/certs/target-ca.crt \
  https://opensearch-cluster-master:9200/_cluster/health

# Verify target cluster certificate validation
kubectl exec -it deployment/replayer -n ma -- \
  openssl s_client -connect opensearch-cluster-master:9200 \
  -cert /etc/ssl/certs/client.crt -key /etc/ssl/private/client.key \
  -CAfile /etc/ssl/certs/target-ca.crt -verify_return_error
```

## 7. mTLS Traffic Analysis

### 7.1 Network Traffic Inspection

```bash
# Capture and analyze mTLS traffic (requires elevated privileges)
kubectl exec -it deployment/capture-proxy -n ma -- \
  tcpdump -i any -s 0 -w /tmp/mtls-traffic.pcap port 9200 or port 9093

# Check TLS handshake in traffic
kubectl exec -it deployment/capture-proxy -n ma -- \
  tcpdump -i any -A port 9200 | grep -E "(Client Hello|Server Hello|Certificate)"
```

### 7.2 Connection State Verification

```bash
# Check established TLS connections
kubectl exec -it deployment/capture-proxy -n ma -- \
  netstat -tlnp | grep -E "(9200|9093|8443)"

# Verify SSL session information
kubectl exec -it deployment/migration-console -n ma -- \
  openssl s_client -connect capture-proxy:9200 \
  -cert /etc/ssl/certs/tls.crt -key /etc/ssl/private/tls.key \
  -CAfile /etc/ssl/certs/ca.crt -sess_out /tmp/ssl_session.pem
```

## 8. Certificate Rotation Verification

### 8.1 Certificate Renewal Testing

```bash
# Check certificate auto-renewal configuration
kubectl describe certificate capture-proxy-tls -n ma | grep -A 5 "Renewal Time"

# Manually trigger certificate renewal (for testing)
kubectl annotate certificate capture-proxy-tls -n ma cert-manager.io/issue-temporary-certificate=""

# Verify new certificate is issued
kubectl get certificate capture-proxy-tls -n ma -w
```

### 8.2 Service Restart on Certificate Update

```bash
# Check if pods restart when certificates are updated
kubectl get events -n ma --field-selector reason=TLSConfigChanged --watch

# Verify certificate hot-reload capability
kubectl exec -it deployment/capture-proxy -n ma -- \
  ls -la /etc/ssl/certs/ /etc/ssl/private/

# Test service availability during certificate rotation
while true; do
  kubectl exec -it deployment/migration-console -n ma -- \
    curl -s --cert /etc/ssl/certs/tls.crt --key /etc/ssl/private/tls.key \
    --cacert /etc/ssl/certs/ca.crt \
    https://capture-proxy:9200/_cluster/health
  sleep 5
done
```

## 9. mTLS Security Validation

### 9.1 Certificate Authority Trust Chain

```bash
# Verify complete trust chain
kubectl get secret migration-ca-key-pair -n cert-manager -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -text | grep -A 5 "Basic Constraints"

# Check intermediate CA if present
kubectl get certificates -n ma -o yaml | grep -A 10 "issuerRef"

# Validate certificate chain depth
for cert in capture-proxy kafka migration-console replayer; do
  echo "=== $cert Chain Depth ==="
  kubectl get secret ${cert}-tls -n ma -o jsonpath='{.data.tls\.crt}' | \
    base64 -d | openssl x509 -noout -text | grep -E "(Subject:|Issuer:)"
done
```

### 9.2 Certificate Revocation Check

```bash
# Check if CRL distribution points are configured
kubectl get secret capture-proxy-tls -n ma -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -text | grep -A 5 "CRL Distribution Points"

# Verify OCSP responder configuration
kubectl get secret capture-proxy-tls -n ma -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -text | grep -A 5 "OCSP"
```

## 10. mTLS Troubleshooting

### 10.1 Common mTLS Issues

```bash
# Certificate not found errors
kubectl logs -l app=capture-proxy -n ma | grep -i "certificate\|tls\|ssl"

# Certificate verification failures
kubectl logs -l app=migration-console -n ma | grep -i "verify\|handshake\|certificate"

# Check certificate file permissions
kubectl exec -it deployment/capture-proxy -n ma -- ls -la /etc/ssl/certs/ /etc/ssl/private/
```

### 10.2 mTLS Handshake Debugging

```bash
# Debug TLS handshake with verbose output
kubectl exec -it deployment/migration-console -n ma -- \
  openssl s_client -connect capture-proxy:9200 -debug \
  -cert /etc/ssl/certs/tls.crt -key /etc/ssl/private/tls.key \
  -CAfile /etc/ssl/certs/ca.crt

# Check cipher suites and protocols
kubectl exec -it deployment/capture-proxy -n ma -- \
  openssl s_client -connect kafka:9093 -cipher 'ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS' \
  -cert /etc/ssl/certs/tls.crt -key /etc/ssl/private/tls.key
```

### 10.3 Configuration Validation

```bash
# Validate SSL configuration syntax
kubectl exec -it deployment/kafka -n ma -- \
  kafka-configs.sh --bootstrap-server localhost:9092 --describe --entity-type brokers --entity-name 0

# Check certificate and key pair matching
kubectl get secret capture-proxy-tls -n ma -o jsonpath='{.data.tls\.crt}' | base64 -d > /tmp/cert.pem
kubectl get secret capture-proxy-tls -n ma -o jsonpath='{.data.tls\.key}' | base64 -d > /tmp/key.pem
openssl x509 -noout -modulus -in /tmp/cert.pem | openssl md5
openssl rsa -noout -modulus -in /tmp/key.pem | openssl md5
```

## 11. mTLS Health Check Script

Create a comprehensive mTLS health check script:

```bash
#!/bin/bash
NAMESPACE="ma"

echo "=== mTLS Health Check for OpenSearch Migrations ==="
echo "Namespace: $NAMESPACE"
echo

# Check certificate status
echo "=== Certificate Status ==="
kubectl get certificates -n $NAMESPACE
echo

# Check certificate expiration
echo "=== Certificate Expiration ==="
for cert in $(kubectl get certificates -n $NAMESPACE -o name); do
  expiry=$(kubectl get $cert -n $NAMESPACE -o jsonpath='{.status.notAfter}')
  echo "$cert expires: $expiry"
done
echo

# Test mTLS connections
echo "=== mTLS Connectivity Tests ==="

# Test internal service mTLS
echo "Testing Migration Console -> Capture Proxy mTLS..."
kubectl exec deployment/migration-console -n $NAMESPACE -- \
  curl -s --cert /etc/ssl/certs/tls.crt --key /etc/ssl/private/tls.key \
  --cacert /etc/ssl/certs/ca.crt \
  https://capture-proxy:9200/_cluster/health > /dev/null 2>&1 && \
  echo "✅ Success" || echo "❌ Failed"

echo "Testing Capture Proxy -> Kafka mTLS..."
kubectl exec deployment/capture-proxy -n $NAMESPACE -- \
  timeout 5 openssl s_client -connect kafka:9093 \
  -cert /etc/ssl/certs/tls.crt -key /etc/ssl/private/tls.key \
  -CAfile /etc/ssl/certs/ca.crt -verify_return_error > /dev/null 2>&1 && \
  echo "✅ Success" || echo "❌ Failed"

echo -e "\n=== mTLS Health Check Complete ==="
```

## 12. mTLS Success Criteria

Your mTLS deployment is secure and functional when:

- ✅ All certificates are issued and valid (`Ready: True`)
- ✅ Certificate chain validation passes
- ✅ Service-to-service mTLS handshakes succeed
- ✅ Client certificates are properly configured for external clusters
- ✅ No certificate verification errors in application logs
- ✅ Certificate rotation works without service interruption
- ✅ Strong cipher suites and protocols are configured
- ✅ Certificate expiration monitoring is in place
- ✅ mTLS connections use proper certificate validation
- ✅ Trust relationships are correctly established
- ✅ Certificate authority chain is properly configured

## 13. Security Best Practices Validation

### 13.1 Certificate Security

```bash
# Check certificate key strength
for secret in $(kubectl get secrets -n ma -o name | grep tls); do
  echo "=== $secret Key Strength ==="
  kubectl get $secret -n ma -o jsonpath='{.data.tls\.key}' | base64 -d | openssl rsa -noout -text | grep "Private-Key"
done

# Verify certificate uses strong signature algorithm
kubectl get secret capture-proxy-tls -n ma -o jsonpath='{.data.tls\.crt}' | \
  base64 -d | openssl x509 -noout -text | grep "Signature Algorithm"
```

### 13.2 TLS Protocol Security

```bash
# Test that weak protocols are disabled
kubectl exec -it deployment/capture-proxy -n ma -- \
  openssl s_client -connect kafka:9093 -ssl3 2>&1 | grep -i "protocol version"

# Verify strong cipher suites only
kubectl exec -it deployment/migration-console -n ma -- \
  openssl s_client -connect capture-proxy:9200 -cipher 'HIGH:!aNULL:!MD5:!3DES' \
  -cert /etc/ssl/certs/tls.crt -key /etc/ssl/private/tls.key 2>&1 | grep "Cipher is"
```

This mTLS verification guide ensures that your OpenSearch Migrations deployment maintains the highest security standards through proper mutual TLS implementation and validation.
