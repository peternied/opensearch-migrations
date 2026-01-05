################################################################################
# ECR Module Outputs
################################################################################

output "repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.this.repository_url
}

output "repository_arn" {
  description = "ARN of the ECR repository"
  value       = aws_ecr_repository.this.arn
}

output "repository_name" {
  description = "Name of the ECR repository"
  value       = aws_ecr_repository.this.name
}

output "registry_id" {
  description = "Registry ID where the repository was created"
  value       = aws_ecr_repository.this.registry_id
}

output "registry_url" {
  description = "Full registry URL (account.dkr.ecr.region.amazonaws.com/repo)"
  value       = "${aws_ecr_repository.this.registry_id}.dkr.ecr.${split(".", aws_ecr_repository.this.repository_url)[3]}.amazonaws.com/${aws_ecr_repository.this.name}"
}
