################################################################################
# Create VPC Environment Variables
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

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.212.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones to use"
  type        = number
  default     = 2
}

variable "enable_ipv6" {
  description = "Enable IPv6 support (dual-stack VPC)"
  type        = bool
  default     = true
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
