################################################################################
# Migration Assistant - Create VPC Environment
#
# This configuration creates a new VPC along with the EKS cluster.
# Use this when you don't have an existing VPC to deploy into.
################################################################################

module "migration_assistant" {
  source = "../../"

  aws_region = var.aws_region
  stage      = var.stage

  # VPC Configuration - Create new VPC
  create_vpc     = true
  vpc_cidr_block = var.vpc_cidr_block
  az_count       = var.az_count
  enable_ipv6    = var.enable_ipv6

  # EKS Configuration
  kubernetes_version      = var.kubernetes_version
  endpoint_private_access = var.endpoint_private_access
  endpoint_public_access  = var.endpoint_public_access
  admin_principal_arn     = var.admin_principal_arn

  # Namespace
  namespace = var.namespace
}
