# OpenSearch Migrations Kubernetes Architecture

This document provides a comprehensive overview of the OpenSearch Migrations system architecture deployed on Kubernetes, including components, network configuration, security posture, and application workflow.

## System Overview

The OpenSearch Migrations K8s deployment provides a comprehensive solution for migrating from Elasticsearch clusters to OpenSearch clusters. There are two main deployment approaches:

1. **Basic Migration Assistant** (`migrationAssistant`) - Core migration services
2. **Advanced Migration Assistant** (`migrationAssistantWithArgo`) - Full-featured with Argo workflows and enhanced observability

## High-Level Architecture

```mermaid
graph TB
    subgraph "Client Applications"
        C1[Client App 1]
        C2[Client App 2] 
        C3[Client App N]
    end
    
    subgraph "Migration Infrastructure"
        MC[Migration Console<br/>Web UI]
        CP[Capture Proxy<br/>:9200]
        K[Kafka Cluster<br/>Traffic Store]
        TR[Traffic Replayer]
        BL[Bulk Document Loader<br/>RFS]
        
        subgraph "Storage"
            SV[Snapshot Volume]
            LV[Logs Volume]
        end
    end
    
    subgraph "Source Environment"
        ES[Elasticsearch Cluster<br/>Source]
    end
    
    subgraph "Target Environment" 
        OS[OpenSearch Cluster<br/>Target]
    end
    
    subgraph "Observability Stack"
        P[Prometheus]
        G[Grafana]
        J[Jaeger]
    end

    C1 --> CP
    C2 --> CP  
    C3 --> CP
    CP --> ES
    CP --> K
    K --> TR
    TR --> OS
    BL --> ES
    BL --> OS
    MC --> CP
    MC --> TR
    MC --> BL
    MC --> K
    BL --> SV
    MC --> LV
    TR --> LV
    
    P --> G
    J --> G
    TR --> J
    CP --> J
```

## Network Configuration

```mermaid
graph LR
    subgraph "External Network"
        EXT[External Clients]
    end
    
    subgraph "Kubernetes Cluster"
        subgraph "Migration Namespace"
            subgraph "Services"
                CPS[capture-proxy-service<br/>:9200]
                MCS[migration-console-service<br/>:8080]
                KS[kafka-service<br/>:9092] 
            end
            
            subgraph "Pods"
                CP[Capture Proxy Pod]
                MC[Migration Console Pod]
                TR[Traffic Replayer Pod]
                K[Kafka Pod]
                BL[Bulk Loader Pod]
            end
        end
        
        subgraph "Source Namespace"
            ESS[elasticsearch-service<br/>:9200]
            ESP[Elasticsearch Pod]
        end
        
        subgraph "Target Namespace"
            OSS[opensearch-service<br/>:9200]
            OSP[OpenSearch Pod]
        end
        
        subgraph "Observability"
            PS[prometheus-service]
            GS[grafana-service]
            JS[jaeger-service]
        end
    end

    EXT --> CPS
    CPS --> CP
    CP --> ESS
    ESS --> ESP
    CP --> KS
    KS --> K
    K --> TR
    TR --> OSS
    OSS --> OSP
    MC --> CP
    MC --> TR
    MC --> BL
    BL --> ESS
    BL --> OSS
```

## Security Posture

```mermaid
graph TD
    subgraph "Authentication & Authorization"
        SA[Service Accounts<br/>RBAC Enabled]
        R[Roles & RoleBindings]
        CM[ClusterRoles & Bindings]
    end
    
    subgraph "Configuration Management"
        CFG[ConfigMaps<br/>Non-sensitive Config]
        SEC[Secrets<br/>Passwords & Certs]
        SC[Shared Configs<br/>Cross-component Settings]
    end
    
    subgraph "Network Security"
        ING[Ingress Controllers<br/>External Access Control]
        SVC[Service Mesh Ready]
        NP[Network Policies<br/>Pod-to-Pod Communication]
    end
    
    subgraph "Data Security"
        PVC[Persistent Volume Claims<br/>Encrypted Storage]
        TLS[TLS/SSL Support<br/>Inter-cluster Communication]
        BA[Basic Auth<br/>Cluster Access]
    end
    
    subgraph "Runtime Security"
        PSP[Pod Security Policies]
        SC2[Security Contexts<br/>Non-root Users]
        RO[Read-only Filesystems]
    end

    SA --> R
    R --> CM
    CFG --> SEC
    SEC --> SC
    ING --> SVC
    SVC --> NP
    PVC --> TLS
    TLS --> BA
    PSP --> SC2
    SC2 --> RO
```

## Application Workflow

```mermaid
sequenceDiagram
    participant Client
    participant CaptureProxy as Capture Proxy
    participant Kafka
    participant SourceES as Source Elasticsearch
    participant Replayer as Traffic Replayer  
    participant TargetOS as Target OpenSearch
    participant Console as Migration Console
    participant BulkLoader as Bulk Document Loader

    Note over Console: Phase 1: Setup & Configuration
    Console->>+SourceES: Validate source cluster
    Console->>+TargetOS: Validate target cluster
    Console->>+Kafka: Initialize traffic topics

    Note over Console: Phase 2: Historical Data Migration
    Console->>+BulkLoader: Start snapshot-based migration
    BulkLoader->>+SourceES: Create/access snapshots
    BulkLoader->>+TargetOS: Reindex documents
    BulkLoader-->>-Console: Migration progress

    Note over Console: Phase 3: Live Traffic Capture
    Console->>+CaptureProxy: Enable traffic capture
    Client->>+CaptureProxy: Send requests
    CaptureProxy->>+SourceES: Forward requests
    SourceES-->>-CaptureProxy: Return responses
    CaptureProxy->>+Kafka: Store captured traffic
    CaptureProxy-->>-Client: Return responses

    Note over Console: Phase 4: Traffic Replay
    Console->>+Replayer: Start traffic replay
    Replayer->>+Kafka: Read captured traffic
    Replayer->>+TargetOS: Replay requests
    TargetOS-->>-Replayer: Return responses
    Replayer-->>-Console: Replay metrics

    Note over Console: Phase 5: Validation & Cutover
    Console->>Console: Compare results
    Console->>Console: Generate migration reports
```

## Key Components Details

### Core Services

- **Migration Console**: Web-based UI for orchestrating migrations, monitoring progress, and managing configurations
- **Capture Proxy**: Transparent proxy that intercepts client traffic to the source cluster and captures it to Kafka
- **Traffic Replayer**: Reads captured traffic from Kafka and replays it against the target cluster with configurable speed
- **Bulk Document Loader (RFS)**: Handles snapshot-based data migration for historical data
- **Kafka Cluster**: Message broker for storing and managing captured traffic

### Infrastructure Services

- **Shared Storage**: Persistent volumes for logs and snapshots
- **Observability**: Optional Prometheus, Grafana, and Jaeger for monitoring and tracing
- **Service Mesh Ready**: Architecture supports Istio/other service mesh implementations

### Advanced Features (Argo variant)

- **Argo Workflows**: Orchestrates complex migration workflows
- **OpenTelemetry**: Advanced observability and tracing
- **FluentBit**: Log aggregation and forwarding
- **LocalStack**: AWS service emulation for testing

## Current Security Implementation

### Authentication & Authorization
- Service accounts with RBAC permissions for each component
- Role-based access control for Kubernetes resources
- Basic authentication for cluster access (configurable)

### Configuration Management
- ConfigMaps for non-sensitive configuration
- Kubernetes Secrets for passwords and certificates
- Shared configuration system for cross-component settings

### Network Security
- Service-to-service communication within cluster
- Ingress controllers for external access control
- Ready for service mesh implementation

## TLS Implementation Roadmap

### Current TLS Status
Based on the current configuration files, TLS implementation is partially prepared but not fully enabled:

1. **Commented TLS Configuration**: SSL config files are referenced but commented out in capture proxy values
2. **Basic Auth Over HTTP**: Currently using basic authentication without TLS
3. **Insecure Connections**: Many components configured with `insecure: true` flags

### TLS Implementation Strategy

#### Phase 1: Certificate Management Infrastructure

```mermaid
graph TD
    subgraph "Certificate Management"
        CM[cert-manager]
        CA[Certificate Authority]
        ACME[ACME Provider<br/>Let's Encrypt]
        SELF[Self-Signed<br/>Internal CA]
    end
    
    subgraph "Certificate Types"
        SC[Service Certificates]
        IC[Ingress Certificates]
        CC[Client Certificates]
        KC[Kafka Certificates]
    end
    
    CM --> CA
    CA --> ACME
    CA --> SELF
    CM --> SC
    CM --> IC
    CM --> CC
    CM --> KC
```

**Implementation Steps:**

1. **Deploy cert-manager** (already available in Argo variant):
   ```yaml
   cert-manager:
     version: 1.17.2
     repository: https://charts.jetstack.io
     values:
       crds:
         enabled: true
   ```

2. **Create ClusterIssuer for internal certificates**:
   ```yaml
   apiVersion: cert-manager.io/v1
   kind: ClusterIssuer
   metadata:
     name: migration-ca-issuer
   spec:
     ca:
       secretName: migration-ca-key-pair
   ```

3. **Generate root CA certificate for internal communication**

#### Phase 2: Inter-Service TLS

```mermaid
graph LR
    subgraph "TLS-Enabled Communications"
        CP[Capture Proxy<br/>:9200 HTTPS]
        K[Kafka<br/>:9093 SSL]
        TR[Traffic Replayer<br/>TLS Client]
        MC[Migration Console<br/>:8443 HTTPS]
    end
    
    subgraph "External Clusters"
        ES[Source ES<br/>HTTPS]
        OS[Target OS<br/>HTTPS]
    end
    
    CP -.->|TLS| K
    K -.->|TLS| TR
    MC -.->|TLS| CP
    MC -.->|TLS| TR
    CP -.->|TLS| ES
    TR -.->|TLS| OS
```

**Required Changes:**

1. **Capture Proxy TLS Configuration**:
   - Enable SSL config file: `/usr/share/elasticsearch/config/proxy_tls.yml`
   - Update service to use HTTPS port 9200
   - Configure client certificate verification

2. **Kafka TLS Configuration**:
   - Enable SSL listeners on port 9093
   - Configure mutual TLS authentication
   - Update all Kafka clients to use SSL

3. **Traffic Replayer TLS**:
   - Configure TLS client certificates for target cluster connections
   - Update authentication headers for HTTPS

4. **Migration Console TLS**:
   - Enable HTTPS on port 8443
   - Configure TLS for web UI access
   - Update ingress controllers for TLS termination

#### Phase 3: External Cluster TLS

**Configuration Updates Needed:**

1. **Update shared configurations to use HTTPS endpoints**:
   ```yaml
   shared-configs:
     globalParameters:
       sourceCluster:
         object:
           endpoint: "https://elasticsearch-master:9200"
           allowInsecure: false  # Change from true
           certFile: "/certs/source-ca.crt"
       targetCluster:
         object:
           endpoint: "https://opensearch-cluster-master:9200" 
           allowInsecure: false  # Change from true
           certFile: "/certs/target-ca.crt"
   ```

2. **Certificate mounting in deployment configurations**

#### Phase 4: Complete TLS Security Model

```mermaid
graph TB
    subgraph "External Access"
        EXT[External Clients]
        ING[Ingress Controller<br/>TLS Termination]
    end
    
    subgraph "Internal Services"
        MC[Migration Console<br/>mTLS]
        CP[Capture Proxy<br/>mTLS]
        TR[Traffic Replayer<br/>mTLS]
        K[Kafka Cluster<br/>mTLS]
    end
    
    subgraph "External Clusters"
        ES[Source Elasticsearch<br/>TLS + Client Auth]
        OS[Target OpenSearch<br/>TLS + Client Auth]
    end
    
    EXT -.->|HTTPS| ING
    ING -.->|mTLS| MC
    MC -.->|mTLS| CP
    MC -.->|mTLS| TR
    CP -.->|mTLS| K
    K -.->|mTLS| TR
    CP -.->|TLS + Client Cert| ES
    TR -.->|TLS + Client Cert| OS
```

### Implementation Checklist

- [ ] **Phase 1: Certificate Infrastructure**
  - [ ] Deploy cert-manager
  - [ ] Create internal CA
  - [ ] Configure ClusterIssuer
  - [ ] Generate service certificates

- [ ] **Phase 2: Service-to-Service TLS**
  - [ ] Enable Kafka SSL/TLS
  - [ ] Configure Capture Proxy HTTPS
  - [ ] Update Traffic Replayer for TLS
  - [ ] Enable Migration Console HTTPS

- [ ] **Phase 3: External Cluster TLS**
  - [ ] Configure source cluster certificates
  - [ ] Configure target cluster certificates
  - [ ] Update connection configurations
  - [ ] Test certificate validation

- [ ] **Phase 4: Security Hardening**
  - [ ] Enable mutual TLS (mTLS) between services
  - [ ] Configure certificate rotation
  - [ ] Implement certificate monitoring
  - [ ] Update security policies

### Configuration Files to Modify

1. **Capture Proxy**: `charts/components/captureProxy/values.yaml`
   - Uncomment and configure `sslConfigFile`
   - Update service definitions for HTTPS

2. **Kafka Cluster**: `charts/sharedResources/baseKafkaCluster/values.yaml`
   - Add SSL listener configuration
   - Configure authentication mechanisms

3. **Traffic Replayer**: `charts/components/replayer/values.yaml`  
   - Add TLS client configuration
   - Update target cluster connection settings

4. **Migration Console**: `charts/components/migrationConsole/values.yaml`
   - Configure HTTPS listener
   - Update ingress for TLS termination

5. **Shared Configurations**: `charts/aggregates/migrationAssistant/values.yaml`
   - Update cluster endpoints to HTTPS
   - Set `allowInsecure: false`
   - Add certificate file paths

This roadmap provides a structured approach to implementing comprehensive TLS security across the OpenSearch Migrations infrastructure while maintaining operational functionality throughout the transition.
