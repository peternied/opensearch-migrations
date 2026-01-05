# Migration Assistant Terraform Deployment - Design Document

## Overview

This document describes the architecture and design decisions for deploying the OpenSearch Migration Assistant infrastructure using Terraform. The deployment targets AWS EKS with Auto Mode, providing a serverless Kubernetes experience with automatic node provisioning.

## Goals

1. **Portability**: Enable deployment in environments where AWS CDK/CloudFormation may not be preferred
2. **Modularity**: Provide reusable, composable modules for different deployment scenarios
3. **Compatibility**: Maintain feature parity with the existing CDK deployment
4. **Simplicity**: Leverage EKS Auto Mode to minimize operational complexity

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Account                                     │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         VPC (10.212.0.0/16)                           │  │
│  │                                                                        │  │
│  │   ┌─────────────────────┐      ┌─────────────────────┐                │  │
│  │   │   Public Subnet 1   │      │   Public Subnet 2   │                │  │
│  │   │   (AZ-a)            │      │   (AZ-b)            │                │  │
│  │   │   ┌─────────────┐   │      │   ┌─────────────┐   │                │  │
│  │   │   │ NAT Gateway │   │      │   │ NAT Gateway │   │                │  │
│  │   │   └─────────────┘   │      │   └─────────────┘   │                │  │
│  │   └─────────────────────┘      └─────────────────────┘                │  │
│  │                                                                        │  │
│  │   ┌─────────────────────┐      ┌─────────────────────┐                │  │
│  │   │  Private Subnet 1   │      │  Private Subnet 2   │                │  │
│  │   │  (AZ-a)             │      │  (AZ-b)             │                │  │
│  │   │                     │      │                     │                │  │
│  │   │  ┌───────────────────────────────────────────┐  │                │  │
│  │   │  │           EKS Auto Mode Cluster           │  │                │  │
│  │   │  │                                           │  │                │  │
│  │   │  │  ┌─────────────┐  ┌─────────────┐        │  │                │  │
│  │   │  │  │   System    │  │   General   │        │  │                │  │
│  │   │  │  │  Node Pool  │  │  Purpose    │        │  │                │  │
│  │   │  │  │             │  │  Node Pool  │        │  │                │  │
│  │   │  │  └─────────────┘  └─────────────┘        │  │                │  │
│  │   │  │                                           │  │                │  │
│  │   │  │  Pod Identity Associations:               │  │                │  │
│  │   │  │  - migrations-service-account             │  │                │  │
│  │   │  │  - argo-workflow-executor                 │  │                │  │
│  │   │  │  - build-images-service-account           │  │                │  │
│  │   │  │  - migration-console-access-role          │  │                │  │
│  │   │  │  - otel-collector                         │  │                │  │
│  │   │  └───────────────────────────────────────────┘  │                │  │
│  │   └─────────────────────┘      └─────────────────────┘                │  │
│  │                                                                        │  │
│  │   VPC Endpoints:                                                       │  │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │  │
│  │   │    S3    │ │   Logs   │ │   EFS    │ │ ECR API  │ │ ECR DKR  │   │  │
│  │   │(Gateway) │ │(Interface│ │(Interface│ │(Interface│ │(Interface│   │  │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌────────────────┐  ┌────────────────────────────────────────────────────┐ │
│  │  ECR Registry  │  │                   IAM Roles                        │ │
│  │  migration-ecr │  │  - EKS Cluster Role (5 managed policies)           │ │
│  │                │  │  - EKS Node Role (3 managed policies)              │ │
│  │                │  │  - Pod Identity Role (migrations workloads)        │ │
│  │                │  │  - Snapshot Role (OpenSearch S3 access)            │ │
│  └────────────────┘  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
deployment/terraform/
├── main.tf                 # Root module - orchestrates all components
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── modules/
│   ├── vpc/                # VPC with subnets, NAT, endpoints
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── eks/                # EKS cluster with Auto Mode
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── iam/                # IAM roles and policies
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── ecr/                # ECR repository
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
└── environments/
    ├── create-vpc/         # Deploy with new VPC
    └── import-vpc/         # Deploy into existing VPC
```

## Component Details

### VPC Module

Creates a production-ready VPC with:

| Component | Configuration |
|-----------|---------------|
| CIDR Block | `10.212.0.0/16` (avoids default VPC conflicts) |
| IP Protocol | Dual-stack (IPv4 + IPv6) |
| Availability Zones | 2 (configurable) |
| Public Subnets | 1 per AZ with Internet Gateway |
| Private Subnets | 1 per AZ with NAT Gateway |
| NAT Gateways | 1 per AZ (HA configuration) |

**VPC Endpoints** (reduce data transfer costs, improve security):
- **S3** (Gateway): Snapshot storage
- **CloudWatch Logs** (Interface): Log aggregation
- **EFS** (Interface): Shared filesystem (FIPS-compatible for GovCloud)
- **ECR API** (Interface): Container registry API
- **ECR Docker** (Interface): Container image pulls

### EKS Module

Deploys an EKS cluster with Auto Mode enabled:

| Feature | Configuration |
|---------|---------------|
| Kubernetes Version | 1.32 |
| Compute Mode | Auto Mode (serverless) |
| Node Pools | `general-purpose`, `system` |
| Authentication | API mode (not ConfigMap) |
| Endpoint Access | Private + Public |
| Block Storage | EBS CSI enabled |
| Load Balancing | ALB/NLB enabled |

**EKS Auto Mode Benefits**:
- No node group management required
- Automatic scaling and provisioning
- Built-in Karpenter-like behavior
- Reduced operational overhead

**Pod Identity Associations** (5 service accounts):

| Service Account | Purpose |
|-----------------|---------|
| `build-images-service-account` | Image building in-cluster |
| `argo-workflow-executor` | Argo workflow pods |
| `migrations-service-account` | General migration workloads |
| `migration-console-access-role` | Migration console StatefulSet |
| `otel-collector` | OpenTelemetry metrics/traces |

### IAM Module

Creates four IAM roles:

#### 1. EKS Cluster Role
Attached managed policies:
- `AmazonEKSClusterPolicy`
- `AmazonEKSBlockStoragePolicy`
- `AmazonEKSComputePolicy`
- `AmazonEKSLoadBalancingPolicy`
- `AmazonEKSNetworkingPolicy`

#### 2. EKS Node Role
Attached managed policies:
- `AmazonEKSWorkerNodePolicy`
- `AmazonEC2ContainerRegistryReadOnly`
- `AmazonEKS_CNI_Policy`

#### 3. Pod Identity Role
Custom policy with permissions for:
- ECR (full access for image operations)
- EFS (mount and write)
- OpenSearch/AOSS (HTTP operations)
- Secrets Manager (read secrets)
- S3 (full bucket operations for migrations)
- CloudWatch Logs (log streaming)
- CloudWatch Metrics (OTEL awsemf exporter)
- X-Ray (trace publishing)
- IAM PassRole (for snapshot operations)

#### 4. Snapshot Role
Assumed by OpenSearch Service for S3 snapshot operations:
- `s3:ListBucket` on `migrations-*`
- `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on `migrations-*/*`

### ECR Module

Creates a private ECR repository for migration container images:

| Feature | Configuration |
|---------|---------------|
| Image Mutability | MUTABLE |
| Scan on Push | Enabled |
| Encryption | AES256 |
| Force Delete | Enabled (cleanup on destroy) |
| Lifecycle Policy | Keep last 30 images |

## Design Decisions

### 1. EKS Auto Mode vs. Managed Node Groups

**Decision**: Use EKS Auto Mode

**Rationale**:
- Eliminates node group management complexity
- Automatic right-sizing of compute resources
- Built-in spot instance support
- Reduces Terraform state complexity
- Matches CDK deployment's modern approach

**Trade-offs**:
- Requires Terraform AWS provider >= 5.82.0
- Less granular control over node specifications
- Newer feature with less community experience

### 2. Pod Identity vs. IRSA

**Decision**: Use EKS Pod Identity

**Rationale**:
- Simpler configuration (no OIDC provider setup)
- Native AWS integration
- Cleaner IAM trust relationships
- Matches CDK deployment approach

**Trade-offs**:
- Requires EKS 1.24+ (not a concern with 1.32)
- Less portable to non-AWS Kubernetes

### 3. Dual-Stack VPC

**Decision**: Enable IPv6 by default

**Rationale**:
- Future-proofs the deployment
- Matches CDK deployment configuration
- No additional cost
- Can be disabled if needed

### 4. Module Granularity

**Decision**: Separate modules for VPC, EKS, IAM, ECR

**Rationale**:
- Enables mix-and-match deployments
- Allows using existing VPCs
- Facilitates testing and maintenance
- Clear separation of concerns

### 5. Environment Configurations

**Decision**: Provide `create-vpc` and `import-vpc` environments

**Rationale**:
- Common deployment patterns
- Reduces configuration errors
- Documents recommended settings
- Easy starting point for customization

## Security Considerations

### Network Security
- Private subnets for workloads
- VPC endpoints reduce internet exposure
- Security groups restrict endpoint access
- NAT gateways for controlled egress

### IAM Security
- Least-privilege policies where practical
- Pod Identity eliminates long-lived credentials
- Separate roles for different purposes
- No wildcard principals

### Container Security
- ECR scan-on-push enabled
- Private registry (not public ECR)
- Image lifecycle policy limits exposure

## Integration with Helm Charts

After Terraform deploys the infrastructure, the existing Helm charts deploy:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Terraform (Phase 1)                          │
│  VPC → IAM → ECR → EKS Cluster → Pod Identity Associations      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Helm Charts (Phase 2)                         │
│  migrationAssistantWithArgo chart:                              │
│  ├── etcd (workflow coordination)                               │
│  ├── cert-manager (TLS)                                         │
│  ├── kube-prometheus-stack (metrics)                            │
│  ├── argo-workflows (orchestration)                             │
│  ├── strimzi-kafka-operator (Kafka)                             │
│  ├── fluent-bit (logs → CloudWatch)                             │
│  ├── otel-collector (metrics → CloudWatch)                      │
│  └── migration-console (StatefulSet)                            │
└─────────────────────────────────────────────────────────────────┘
```

The Terraform outputs provide all values needed for Helm deployment:
- `migrations_export_string`: Environment variables for bootstrap script
- `configure_kubectl`: Command to configure kubectl
- `ecr_registry_url`: Registry for custom images
- `snapshot_role_arn`: For OpenSearch snapshot configuration

## Future Enhancements

### Phase 2: Helm Provider Integration
- Add Terraform Helm provider for chart deployment
- Create `helm` module for migration assistant chart
- Enable full infrastructure-as-code deployment

### Additional Modules
- **monitoring**: CloudWatch dashboards and alarms
- **backup**: S3 buckets for snapshots
- **networking**: Transit Gateway integration

### Multi-Region Support
- Remote state configuration
- Cross-region replication
- Global accelerator integration

## Version Requirements

| Component | Minimum Version |
|-----------|-----------------|
| Terraform | >= 1.5.0 |
| AWS Provider | >= 5.82.0 |
| Kubernetes | 1.32 |

## References

- [EKS Auto Mode Documentation](https://docs.aws.amazon.com/eks/latest/userguide/automode.html)
- [EKS Pod Identity](https://docs.aws.amazon.com/eks/latest/userguide/pod-identities.html)
- [Migration Assistant CDK Source](../migration-assistant-solution/)
- [Migration Assistant Helm Charts](../k8s/charts/)
