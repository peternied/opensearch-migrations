################################################################################
# IAM Module Outputs
################################################################################

output "cluster_role_arn" {
  description = "ARN of the EKS cluster IAM role"
  value       = aws_iam_role.eks_cluster.arn
}

output "cluster_role_name" {
  description = "Name of the EKS cluster IAM role"
  value       = aws_iam_role.eks_cluster.name
}

output "node_role_arn" {
  description = "ARN of the EKS node IAM role"
  value       = aws_iam_role.eks_node.arn
}

output "node_role_name" {
  description = "Name of the EKS node IAM role"
  value       = aws_iam_role.eks_node.name
}

output "pod_identity_role_arn" {
  description = "ARN of the pod identity IAM role for migrations"
  value       = aws_iam_role.pod_identity.arn
}

output "pod_identity_role_name" {
  description = "Name of the pod identity IAM role for migrations"
  value       = aws_iam_role.pod_identity.name
}

output "snapshot_role_arn" {
  description = "ARN of the snapshot IAM role for OpenSearch"
  value       = aws_iam_role.snapshot.arn
}

output "snapshot_role_name" {
  description = "Name of the snapshot IAM role for OpenSearch"
  value       = aws_iam_role.snapshot.name
}
