################################################################################
# EKS Module Variables
################################################################################

variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.32"
}

variable "cluster_role_arn" {
  description = "ARN of the IAM role for the EKS cluster"
  type        = string
}

variable "node_role_arn" {
  description = "ARN of the IAM role for EKS Auto Mode nodes"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for the EKS cluster"
  type        = list(string)
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

variable "additional_security_group_ids" {
  description = "Additional security group IDs to attach to the cluster"
  type        = list(string)
  default     = []
}

variable "node_pools" {
  description = "List of node pools for EKS Auto Mode"
  type        = list(string)
  default     = ["general-purpose", "system"]
}

variable "support_type" {
  description = "EKS support type (STANDARD or EXTENDED)"
  type        = string
  default     = "STANDARD"
}

variable "pod_identity_associations" {
  description = "Map of pod identity associations"
  type = map(object({
    namespace       = string
    service_account = string
    role_arn        = string
  }))
  default = {}
}

variable "admin_principal_arn" {
  description = "ARN of the principal (user/role) to grant cluster admin access"
  type        = string
  default     = null
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
