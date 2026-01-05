################################################################################
# Migration Assistant - Import VPC Environment
#
# This configuration uses an existing VPC and subnets.
# Use this when you have an existing VPC you want to deploy into.
################################################################################

module "migration_assistant" {
  source = "../../"

  aws_region = var.aws_region
  stage      = var.stage

  # VPC Configuration - Use existing VPC
  create_vpc = false
  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  # EKS Configuration
  kubernetes_version      = var.kubernetes_version
  endpoint_private_access = var.endpoint_private_access
  endpoint_public_access  = var.endpoint_public_access
  admin_principal_arn     = var.admin_principal_arn

  # Namespace
  namespace = var.namespace
}
