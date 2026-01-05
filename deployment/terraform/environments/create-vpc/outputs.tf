################################################################################
# Create VPC Environment Outputs
################################################################################

output "eks_cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.migration_assistant.eks_cluster_name
}

output "eks_cluster_endpoint" {
  description = "Endpoint URL for the EKS cluster API server"
  value       = module.migration_assistant.eks_cluster_endpoint
}

output "vpc_id" {
  description = "ID of the created VPC"
  value       = module.migration_assistant.vpc_id
}

output "ecr_registry_url" {
  description = "Full ECR registry URL for image pushes"
  value       = module.migration_assistant.ecr_registry_url
}

output "snapshot_role_arn" {
  description = "ARN of the snapshot role for OpenSearch"
  value       = module.migration_assistant.snapshot_role_arn
}

output "migrations_export_string" {
  description = "Export string for Migration Assistant bootstrap"
  value       = module.migration_assistant.migrations_export_string
}

output "configure_kubectl" {
  description = "Command to configure kubectl"
  value       = module.migration_assistant.configure_kubectl
}
