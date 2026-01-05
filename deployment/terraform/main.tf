################################################################################
# Migration Assistant for OpenSearch - Terraform Root Module
#
# This module deploys the infrastructure required for the Migration Assistant
# on AWS EKS with Auto Mode enabled.
################################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.82.0" # Required for EKS Auto Mode support
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "migration-assistant"
      Environment = var.stage
      ManagedBy   = "terraform"
    }
  }
}

################################################################################
# Local Variables
################################################################################

locals {
  name_prefix      = "migration-assistant-${var.stage}-${var.aws_region}"
  eks_cluster_name = "migration-eks-cluster-${var.stage}-${var.aws_region}"
  ecr_repo_name    = "migration-ecr-${var.stage}-${var.aws_region}"

  # Service account names for pod identity associations
  namespace                              = var.namespace
  build_images_service_account_name      = "build-images-service-account"
  argo_workflow_service_account_name     = "argo-workflow-executor"
  migrations_service_account_name        = "migrations-service-account"
  migration_console_service_account_name = "migration-console-access-role"
  otel_collector_service_account_name    = "otel-collector"

  common_tags = {
    Stage  = var.stage
    Region = var.aws_region
  }
}

################################################################################
# IAM Module
################################################################################

module "iam" {
  source = "./modules/iam"

  name_prefix = local.eks_cluster_name
  tags        = local.common_tags
}

################################################################################
# VPC Module (conditional)
################################################################################

module "vpc" {
  count  = var.create_vpc ? 1 : 0
  source = "./modules/vpc"

  name_prefix        = local.name_prefix
  aws_region         = var.aws_region
  cidr_block         = var.vpc_cidr_block
  az_count           = var.az_count
  enable_ipv6        = var.enable_ipv6
  eks_cluster_name   = local.eks_cluster_name
  use_fips_endpoints = var.use_fips_endpoints
  tags               = local.common_tags
}

################################################################################
# ECR Module
################################################################################

module "ecr" {
  source = "./modules/ecr"

  repository_name         = local.ecr_repo_name
  force_delete            = true
  enable_lifecycle_policy = true
  max_image_count         = 30
  tags                    = local.common_tags
}

################################################################################
# EKS Module
################################################################################

module "eks" {
  source = "./modules/eks"

  cluster_name     = local.eks_cluster_name
  cluster_role_arn = module.iam.cluster_role_arn
  node_role_arn    = module.iam.node_role_arn

  # Use created VPC subnets or provided subnet IDs
  subnet_ids = var.create_vpc ? module.vpc[0].private_subnet_ids : var.subnet_ids

  kubernetes_version      = var.kubernetes_version
  endpoint_private_access = var.endpoint_private_access
  endpoint_public_access  = var.endpoint_public_access
  node_pools              = var.node_pools
  admin_principal_arn     = var.admin_principal_arn

  # Pod Identity Associations
  pod_identity_associations = {
    build_images = {
      namespace       = local.namespace
      service_account = local.build_images_service_account_name
      role_arn        = module.iam.pod_identity_role_arn
    }
    argo_workflow = {
      namespace       = local.namespace
      service_account = local.argo_workflow_service_account_name
      role_arn        = module.iam.pod_identity_role_arn
    }
    migrations = {
      namespace       = local.namespace
      service_account = local.migrations_service_account_name
      role_arn        = module.iam.pod_identity_role_arn
    }
    migration_console = {
      namespace       = local.namespace
      service_account = local.migration_console_service_account_name
      role_arn        = module.iam.pod_identity_role_arn
    }
    otel_collector = {
      namespace       = local.namespace
      service_account = local.otel_collector_service_account_name
      role_arn        = module.iam.pod_identity_role_arn
    }
  }

  tags = local.common_tags

  depends_on = [module.iam]
}
