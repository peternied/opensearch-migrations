# Migration Assistant for OpenSearch - Terraform Deployment

Deploy the OpenSearch Migration Assistant infrastructure on AWS EKS using Terraform.

## Overview

This Terraform configuration deploys the infrastructure required to run the Migration Assistant on a managed Kubernetes cluster (AWS EKS with Auto Mode). It creates:

- **VPC** (optional): Dual-stack VPC with public/private subnets and VPC endpoints
- **EKS Cluster**: Kubernetes 1.32 with Auto Mode (serverless compute)
- **IAM Roles**: Cluster, node, pod identity, and snapshot roles
- **ECR Repository**: Private container registry for migration images
- **Pod Identity Associations**: AWS credentials for Kubernetes workloads

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.5.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- AWS account with permissions to create EKS, VPC, IAM, and ECR resources

## Quick Start

### Option 1: Create New VPC

Use this option if you don't have an existing VPC:

```bash
cd deployment/terraform/environments/create-vpc

# Copy and edit the example tfvars
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your settings

# Initialize and apply
terraform init
terraform plan
terraform apply
```

### Option 2: Use Existing VPC

Use this option to deploy into an existing VPC:

```bash
cd deployment/terraform/environments/import-vpc

# Copy and edit the example tfvars
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your VPC ID and subnet IDs

# Initialize and apply
terraform init
terraform plan
terraform apply
```

## Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `aws_region` | AWS region to deploy into | `us-west-2` |
| `stage` | Environment name (used in resource naming) | `dev`, `prod` |

### VPC Variables (create-vpc only)

| Variable | Description | Default |
|----------|-------------|---------|
| `vpc_cidr_block` | CIDR block for VPC | `10.212.0.0/16` |
| `az_count` | Number of availability zones | `2` |
| `enable_ipv6` | Enable dual-stack (IPv6) | `true` |

### VPC Variables (import-vpc only)

| Variable | Description | Required |
|----------|-------------|----------|
| `vpc_id` | ID of existing VPC | Yes |
| `subnet_ids` | List of subnet IDs (min 2, different AZs) | Yes |

### EKS Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `kubernetes_version` | Kubernetes version | `1.32` |
| `endpoint_private_access` | Enable private API endpoint | `true` |
| `endpoint_public_access` | Enable public API endpoint | `true` |
| `admin_principal_arn` | IAM principal for cluster admin | `null` |
| `namespace` | Kubernetes namespace for workloads | `ma` |

## Outputs

After successful deployment, Terraform provides these outputs:

| Output | Description |
|--------|-------------|
| `eks_cluster_name` | Name of the EKS cluster |
| `eks_cluster_endpoint` | API server endpoint URL |
| `ecr_registry_url` | ECR repository URL for images |
| `snapshot_role_arn` | IAM role for OpenSearch snapshots |
| `migrations_export_string` | Environment variables for bootstrap |
| `configure_kubectl` | Command to configure kubectl |

## Post-Deployment: Install Migration Assistant

After Terraform creates the infrastructure, install the Migration Assistant using Helm:

### 1. Configure kubectl

```bash
# Use the command from Terraform output
$(terraform output -raw configure_kubectl)
```

### 2. Set Environment Variables

```bash
# Export the variables from Terraform output
eval "$(terraform output -raw migrations_export_string)"
```

### 3. Run Bootstrap Script

```bash
# Navigate to the k8s deployment directory
cd ../../../k8s/aws

# Run the bootstrap script (skips infrastructure since Terraform created it)
./aws-bootstrap.sh --skip-git-pull
```

Or manually install with Helm:

```bash
# Create namespace
kubectl create namespace ma

# Install the chart
helm install ma ../charts/aggregates/migrationAssistantWithArgo \
  --namespace ma \
  -f ../charts/aggregates/migrationAssistantWithArgo/values.yaml \
  -f ../charts/aggregates/migrationAssistantWithArgo/valuesEks.yaml \
  --set stageName="${STAGE}" \
  --set aws.region="${AWS_CFN_REGION}" \
  --set aws.account="${AWS_ACCOUNT}" \
  --set defaultBucketConfiguration.snapshotRoleArn="${SNAPSHOT_ROLE}"
```

### 4. Access Migration Console

```bash
kubectl -n ma exec -it migration-console-0 -- /bin/bash
```

## Module Structure

```
terraform/
├── main.tf              # Root module
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── DESIGN.md            # Architecture documentation
├── README.md            # This file
├── modules/
│   ├── vpc/             # VPC resources
│   ├── eks/             # EKS cluster
│   ├── iam/             # IAM roles and policies
│   └── ecr/             # ECR repository
└── environments/
    ├── create-vpc/      # New VPC deployment
    └── import-vpc/      # Existing VPC deployment
```

## Using Modules Independently

You can use individual modules in your own Terraform configurations:

```hcl
module "migration_iam" {
  source = "github.com/opensearch-project/opensearch-migrations//deployment/terraform/modules/iam"

  name_prefix = "my-migration"
  tags        = { Environment = "prod" }
}

module "migration_eks" {
  source = "github.com/opensearch-project/opensearch-migrations//deployment/terraform/modules/eks"

  cluster_name     = "my-migration-cluster"
  cluster_role_arn = module.migration_iam.cluster_role_arn
  node_role_arn    = module.migration_iam.node_role_arn
  subnet_ids       = ["subnet-abc123", "subnet-def456"]

  pod_identity_associations = {
    migrations = {
      namespace       = "ma"
      service_account = "migrations-service-account"
      role_arn        = module.migration_iam.pod_identity_role_arn
    }
  }
}
```

## Cleanup

To destroy all resources:

```bash
# First, uninstall Helm releases
helm uninstall ma -n ma

# Then destroy Terraform resources
terraform destroy
```

## Troubleshooting

### EKS Cluster Access Denied

If you can't access the cluster after creation:

```bash
# Ensure you're using the correct AWS credentials
aws sts get-caller-identity

# The cluster creator has admin access by default
# To grant access to another role/user, set admin_principal_arn variable
```

### Terraform Provider Version Error

If you see errors about EKS Auto Mode:

```bash
# Ensure AWS provider is >= 5.82.0
terraform providers

# Update providers
terraform init -upgrade
```

### VPC Endpoint Errors in GovCloud

For AWS GovCloud deployments:

```hcl
# Enable FIPS endpoints
use_fips_endpoints = true
```

## Comparison with CDK Deployment

| Feature | Terraform | CDK |
|---------|-----------|-----|
| Infrastructure | Identical | Identical |
| State Management | Terraform state | CloudFormation |
| VPC Options | Create or Import | Create or Import |
| EKS Mode | Auto Mode | Auto Mode |
| IAM Approach | Pod Identity | Pod Identity |
| Helm Deployment | Manual (Phase 2) | Bootstrap script |

## Contributing

See [DESIGN.md](./DESIGN.md) for architecture details and design decisions.

## License

Apache License 2.0 - See [LICENSE](../../LICENSE) for details.
