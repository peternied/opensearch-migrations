################################################################################
# Migration Assistant Terraform Outputs
################################################################################

#------------------------------------------------------------------------------
# EKS Cluster Outputs
#------------------------------------------------------------------------------

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint URL for the EKS cluster API server"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_security_group_id" {
  description = "Security group ID of the EKS cluster"
  value       = module.eks.cluster_security_group_id
}

output "eks_cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data for the cluster"
  value       = module.eks.cluster_certificate_authority_data
  sensitive   = true
}

#------------------------------------------------------------------------------
# VPC Outputs (when created)
#------------------------------------------------------------------------------

output "vpc_id" {
  description = "ID of the VPC"
  value       = var.create_vpc ? module.vpc[0].vpc_id : var.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = var.create_vpc ? module.vpc[0].private_subnet_ids : var.subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = var.create_vpc ? module.vpc[0].public_subnet_ids : []
}

#------------------------------------------------------------------------------
# ECR Outputs
#------------------------------------------------------------------------------

output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = module.ecr.repository_url
}

output "ecr_registry_url" {
  description = "Full ECR registry URL for image pushes"
  value       = module.ecr.registry_url
}

#------------------------------------------------------------------------------
# IAM Outputs
#------------------------------------------------------------------------------

output "snapshot_role_arn" {
  description = "ARN of the snapshot role for OpenSearch"
  value       = module.iam.snapshot_role_arn
}

output "pod_identity_role_arn" {
  description = "ARN of the pod identity role for migrations"
  value       = module.iam.pod_identity_role_arn
}

#------------------------------------------------------------------------------
# Export String (compatible with CDK deployment)
#------------------------------------------------------------------------------

output "migrations_export_string" {
  description = "Export string with all environment variables for Migration Assistant bootstrap"
  value       = <<-EOT
export MIGRATIONS_EKS_CLUSTER_NAME=${module.eks.cluster_name}
export MIGRATIONS_ECR_REGISTRY=${module.ecr.registry_url}
export AWS_ACCOUNT=${data.aws_caller_identity.current.account_id}
export AWS_CFN_REGION=${var.aws_region}
export VPC_ID=${var.create_vpc ? module.vpc[0].vpc_id : var.vpc_id}
export EKS_CLUSTER_SECURITY_GROUP=${module.eks.cluster_security_group_id}
export SNAPSHOT_ROLE=${module.iam.snapshot_role_arn}
export STAGE=${var.stage}
EOT
}

#------------------------------------------------------------------------------
# Kubeconfig Command
#------------------------------------------------------------------------------

output "configure_kubectl" {
  description = "Command to configure kubectl for the EKS cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

#------------------------------------------------------------------------------
# Data Sources
#------------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
