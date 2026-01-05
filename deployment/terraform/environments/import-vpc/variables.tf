################################################################################
# Import VPC Environment Variables
################################################################################

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "stage" {
  description = "Stage/environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "vpc_id" {
  description = "ID of the existing VPC to use"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for EKS (at least 2 in different AZs)"
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "At least 2 subnet IDs are required for EKS."
  }
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.32"
}

variable "endpoint_private_access" {
  description = "Enable private API server endpoint"
  type        = bool
  default     = true
}

variable "endpoint_public_access" {
  description = "Enable public API server endpoint"
  type        = bool
  default     = true
}

variable "admin_principal_arn" {
  description = "ARN of IAM principal to grant EKS cluster admin access"
  type        = string
  default     = null
}

variable "namespace" {
  description = "Kubernetes namespace for Migration Assistant workloads"
  type        = string
  default     = "ma"
}
