################################################################################
# Migration Assistant Terraform Variables
################################################################################

#------------------------------------------------------------------------------
# Required Variables
#------------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
}

variable "stage" {
  description = "Stage/environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

#------------------------------------------------------------------------------
# VPC Configuration
#------------------------------------------------------------------------------

variable "create_vpc" {
  description = "Whether to create a new VPC or use an existing one"
  type        = bool
  default     = true
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC (only used if create_vpc is true)"
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

variable "use_fips_endpoints" {
  description = "Use FIPS-compliant VPC endpoints (required for GovCloud)"
  type        = bool
  default     = false
}

# Required when create_vpc = false
variable "vpc_id" {
  description = "ID of existing VPC (required if create_vpc is false)"
  type        = string
  default     = null
}

variable "subnet_ids" {
  description = "List of subnet IDs for EKS (required if create_vpc is false)"
  type        = list(string)
  default     = []
}

#------------------------------------------------------------------------------
# EKS Configuration
#------------------------------------------------------------------------------

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

variable "node_pools" {
  description = "List of node pools for EKS Auto Mode"
  type        = list(string)
  default     = ["general-purpose", "system"]
}

variable "admin_principal_arn" {
  description = "ARN of IAM principal to grant EKS cluster admin access (optional)"
  type        = string
  default     = null
}

#------------------------------------------------------------------------------
# Namespace Configuration
#------------------------------------------------------------------------------

variable "namespace" {
  description = "Kubernetes namespace for Migration Assistant workloads"
  type        = string
  default     = "ma"
}
