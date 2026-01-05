################################################################################
# EKS Module for Migration Assistant
# Creates an EKS cluster with Auto Mode enabled (serverless compute)
################################################################################

data "aws_caller_identity" "current" {}

locals {
  cluster_name = var.cluster_name
}

################################################################################
# EKS Cluster
################################################################################

resource "aws_eks_cluster" "this" {
  name     = local.cluster_name
  version  = var.kubernetes_version
  role_arn = var.cluster_role_arn

  vpc_config {
    subnet_ids              = var.subnet_ids
    endpoint_private_access = var.endpoint_private_access
    endpoint_public_access  = var.endpoint_public_access
    security_group_ids      = var.additional_security_group_ids
  }

  access_config {
    authentication_mode = "API"
  }

  # EKS Auto Mode configuration
  compute_config {
    enabled       = true
    node_pools    = var.node_pools
    node_role_arn = var.node_role_arn
  }

  # Block storage (EBS CSI) configuration
  storage_config {
    block_storage {
      enabled = true
    }
  }

  # Elastic Load Balancing configuration
  kubernetes_network_config {
    elastic_load_balancing {
      enabled = true
    }
  }

  upgrade_policy {
    support_type = var.support_type
  }

  tags = merge(var.tags, {
    Name = local.cluster_name
  })

  depends_on = [var.cluster_role_arn]
}

################################################################################
# EKS Pod Identity Associations
################################################################################

resource "aws_eks_pod_identity_association" "this" {
  for_each = var.pod_identity_associations

  cluster_name    = aws_eks_cluster.this.name
  namespace       = each.value.namespace
  service_account = each.value.service_account
  role_arn        = each.value.role_arn

  tags = var.tags

  depends_on = [aws_eks_cluster.this]
}

################################################################################
# EKS Access Entry for cluster admin
################################################################################

resource "aws_eks_access_entry" "admin" {
  count = var.admin_principal_arn != null ? 1 : 0

  cluster_name  = aws_eks_cluster.this.name
  principal_arn = var.admin_principal_arn
  type          = "STANDARD"

  tags = var.tags
}

resource "aws_eks_access_policy_association" "admin" {
  count = var.admin_principal_arn != null ? 1 : 0

  cluster_name  = aws_eks_cluster.this.name
  principal_arn = var.admin_principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.admin]
}
