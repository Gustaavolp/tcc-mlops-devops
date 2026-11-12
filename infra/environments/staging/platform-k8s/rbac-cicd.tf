# ==============================================================================
# RBAC do CI/CD
# ==============================================================================
# Permissões mínimas para os pipelines implantarem no namespace fraud-detection.
# As roles IAM do CodeBuild (stack infra/cicd) recebem uma EKS Access Entry com
# o grupo Kubernetes "cicd-deployers", vinculado a esta Role. As políticas de
# acesso nativas do EKS (Edit/Admin) não cobrem os CRDs ScaledObject (KEDA) e
# TargetGroupBinding (AWS Load Balancer Controller), aplicados pelo deploy.
# ==============================================================================

resource "kubernetes_role_v1" "cicd_deployer" {
  metadata {
    name      = "cicd-deployer"
    namespace = kubernetes_namespace_v1.fraud_detection.metadata[0].name
  }

  # Manifestos aplicados pelo deploy (pipelines/scripts/deploy.sh)
  rule {
    api_groups = [""]
    resources  = ["configmaps", "services", "serviceaccounts"]
    verbs      = ["get", "list", "watch", "create", "update", "patch"]
  }
  rule {
    api_groups = ["apps"]
    resources  = ["deployments"]
    verbs      = ["get", "list", "watch", "create", "update", "patch"]
  }
  rule {
    api_groups = ["autoscaling"]
    resources  = ["horizontalpodautoscalers"]
    verbs      = ["get", "list", "watch", "create", "update", "patch"]
  }
  rule {
    api_groups = ["policy"]
    resources  = ["poddisruptionbudgets"]
    verbs      = ["get", "list", "watch", "create", "update", "patch"]
  }
  rule {
    api_groups = ["keda.sh"]
    resources  = ["scaledobjects"]
    verbs      = ["get", "list", "watch", "create", "update", "patch"]
  }
  rule {
    api_groups = ["elbv2.k8s.aws"]
    resources  = ["targetgroupbindings"]
    verbs      = ["get", "list", "watch", "create", "update", "patch"]
  }

  # rollout status / undo / restart
  rule {
    api_groups = ["apps"]
    resources  = ["replicasets"]
    verbs      = ["get", "list", "watch"]
  }
  rule {
    api_groups = [""]
    resources  = ["pods"]
    verbs      = ["get", "list", "watch"]
  }
}

resource "kubernetes_role_binding_v1" "cicd_deployer" {
  metadata {
    name      = "cicd-deployer"
    namespace = kubernetes_namespace_v1.fraud_detection.metadata[0].name
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role_v1.cicd_deployer.metadata[0].name
  }

  subject {
    kind      = "Group"
    name      = "cicd-deployers"
    api_group = "rbac.authorization.k8s.io"
  }
}
