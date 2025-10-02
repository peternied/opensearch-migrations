# Scratch pad

```bash

```

#### Extract a cluster sert from `abc-cluster-ca-cert` on kubernetes
```bash
kubectl -n ma get secret abc-cluster-ca-cert \
  -o jsonpath='{.data.ca\.crt}' | base64 -d > cluster-ca.crt
```

#### Create a jsk store for the cluster cert
```bash
keytool -import -file cluster-ca.crt -alias cluster-ca \
  -keystore client.truststore.jks \
  -storepass changeit -noprompt
```

#### Start the capture proxy with a sample kafka config
```bash
./gradlew TrafficCapture:trafficCaptureProxyServer:run --args="--kafkaConfigFile /home/ubuntu/git/opensearch-migrations/producer.props --kafkaConnection localhost:9092 --listenPort 9054 --destinationUri http://localhost:9200"
```


```mermaid
flowchart TD
  %% Trigger
  A[Deployment<br/>Helm/Argo submit] --> B[Argo WorkflowTemplate: setupKafka]

  subgraph SG1 [Bootstrap via Argo]
    direction TB
    B --> C[Create Kafka Cluster<br/>e.g., Strimzi]
    C --> D[Create Kafka Topics]
  end

  subgraph SG2 [Credentials & configuration]
    direction TB
    C --> E[Create Kafka Users<br/>proxy, replayer, console]
    E --> F[Generate kafka.properties<br/>for each user]
    F --> G[Create/Update K8s Secrets<br/>kafka-properties-<svc>]
  end

  subgraph SG3 [Workload rollout]
    direction TB
  G --> I[Deploy Proxy / Replayer / Console]
  I --> J[Mount Secret as file<br/>e.g., /etc/kafka/kafka.properties]
  J --> K[Add new param to apps]
  K --> L[Services authenticate to Kafka<br/>SASL_SSL creds from properties]
  end


```