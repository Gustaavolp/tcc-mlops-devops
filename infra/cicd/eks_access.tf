# ==============================================================================
# Acesso dos CodeBuild aos clusters EKS (EKS Access Entries)
# ==============================================================================
# - deploy de aplicação e rollout do modelo: grupo Kubernetes "cicd-deployers",
#   ligado à Role cicd-deployer do namespace (platform-k8s/rbac-cicd.tf);
# - Terraform (stack platform-k8s usa os providers helm/kubernetes): cluster admin.
# ==============================================================================

locals {
  deployer_roles = {
    app     = aws_iam_role.codebuild_app.arn
    rollout = aws_iam_role.model_rollout.arn
  }
}

# ---------------------------------------------------------------------- dev
resource "aws_eks_access_entry" "deployer_dev" {
  for_each          = local.deployer_roles
  cluster_name      = local.platform["dev"].eks_cluster_name
  principal_arn     = each.value
  kubernetes_groups = ["cicd-deployers"]
}

resource "aws_eks_access_entry" "infra_dev" {
  cluster_name  = local.platform["dev"].eks_cluster_name
  principal_arn = aws_iam_role.codebuild_infra.arn
}

resource "aws_eks_access_policy_association" "infra_dev" {
  cluster_name  = local.platform["dev"].eks_cluster_name
  principal_arn = aws_eks_access_entry.infra_dev.principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }
}

# ------------------------------------------------------------------ staging
resource "aws_eks_access_entry" "deployer_staging" {
  provider          = aws.staging
  for_each          = local.deployer_roles
  cluster_name      = local.platform["staging"].eks_cluster_name
  principal_arn     = each.value
  kubernetes_groups = ["cicd-deployers"]
}

resource "aws_eks_access_entry" "infra_staging" {
  provider      = aws.staging
  cluster_name  = local.platform["staging"].eks_cluster_name
  principal_arn = aws_iam_role.codebuild_infra.arn
}

resource "aws_eks_access_policy_association" "infra_staging" {
  provider      = aws.staging
  cluster_name  = local.platform["staging"].eks_cluster_name
  principal_arn = aws_eks_access_entry.infra_staging.principal_arn
  policy_arn    = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }
}
