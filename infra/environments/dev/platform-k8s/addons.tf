# ==============================================================================
# Kubernetes Add-ons via Helm
# ==============================================================================
# Este arquivo gerencia add-ons do Kubernetes instalados via Helm.
# Garante que componentes essenciais sejam criados automaticamente com o cluster.
#
# NOTA: Movido de platform/k8s-addons.tf para stack separada (2026-01-18)
# ==============================================================================

# ==============================================================================
# Metrics Server
# ==============================================================================
# Metrics Server coleta métricas de recursos (CPU/Memory) dos nodes e pods.
# Necessário para:
#   - HorizontalPodAutoscaler (HPA)
#   - kubectl top nodes/pods
#   - Vertical Pod Autoscaler (VPA)
# ==============================================================================

resource "helm_release" "metrics_server" {
  name       = "metrics-server"
  repository = "https://kubernetes-sigs.github.io/metrics-server/"
  chart      = "metrics-server"
  version    = "3.13.0" # Atualizado em 2026-02-03
  namespace  = "kube-system"

  set = [
    # Configurações do Metrics Server
    {
      name  = "args[0]"
      value = "--kubelet-preferred-address-types=InternalIP"
    },
    # Replica count para HA (1 em dev, 2+ em prod)
    {
      name  = "replicas"
      value = var.environment == "dev" ? 1 : 2
    },
    # Resource requests/limits
    {
      name  = "resources.requests.cpu"
      value = "100m"
    },
    {
      name  = "resources.requests.memory"
      value = "200Mi"
    },
    {
      name  = "resources.limits.cpu"
      value = "200m"
    },
    {
      name  = "resources.limits.memory"
      value = "400Mi"
    },
  ]
}

# ==============================================================================
# Namespace para aplicações de Fraud Detection
# ==============================================================================
# Cria o namespace fraud-detection se não existir.
# Isso garante que o namespace esteja disponível para deployments.
# ==============================================================================

resource "kubernetes_namespace_v1" "fraud_detection" {
  metadata {
    name = "fraud-detection"

    labels = {
      name        = "fraud-detection"
      environment = var.environment
      managed-by  = "terraform"
    }
  }
}

# ==============================================================================
# Cluster Autoscaler
# ==============================================================================
# Cluster Autoscaler ajusta automaticamente o número de nodes no cluster EKS
# baseado na demanda de pods. Escala nodes para cima quando pods não podem ser
# agendados e para baixo quando nodes estão subutilizados.
#
# NOTA: IRSA está desabilitado devido a SCP. O Autoscaler usa IAM role do node
# que já tem AutoScalingFullAccess policy anexada.
# ==============================================================================

resource "helm_release" "cluster_autoscaler" {
  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  chart      = "cluster-autoscaler"
  version    = "9.55.0" # Atualizado em 2026-02-03
  namespace  = "kube-system"

  set = [
    # ===========================================================================
    # Configuração do Cluster
    # ===========================================================================
    {
      name  = "autoDiscovery.clusterName"
      value = local.eks_cluster_name
    },
    {
      name  = "awsRegion"
      value = var.aws_region
    },
    # ===========================================================================
    # Configurações de Scaling
    # ===========================================================================
    # Tempo de espera antes de remover um node subutilizado (default: 10m)
    # 5m é mais agressivo, adequado para workloads com variação rápida
    {
      name  = "extraArgs.scale-down-delay-after-add"
      value = "5m"
    },
    {
      name  = "extraArgs.scale-down-delay-after-delete"
      value = "0s"
    },
    {
      name  = "extraArgs.scale-down-delay-after-failure"
      value = "3m"
    },
    # Node é considerado subutilizado se uso < 50% (CPU e Memory)
    {
      name  = "extraArgs.scale-down-utilization-threshold"
      value = "0.5"
    },
    # Tempo que node precisa estar subutilizado antes de scale-down (default: 10m)
    {
      name  = "extraArgs.scale-down-unneeded-time"
      value = "5m"
    },
    # Máximo de nodes que podem ser removidos simultaneamente
    {
      name  = "extraArgs.max-node-provision-time"
      value = "10m"
    },
    # Balance similar node groups (distribui pods uniformemente)
    {
      name  = "extraArgs.balance-similar-node-groups"
      value = "true"
    },
    # Skip nodes com pods do sistema (kube-system) durante scale-down
    {
      name  = "extraArgs.skip-nodes-with-system-pods"
      value = "false"
    },
    # ===========================================================================
    # Resources
    # ===========================================================================
    {
      name  = "resources.requests.cpu"
      value = "100m"
    },
    {
      name  = "resources.requests.memory"
      value = "300Mi"
    },
    {
      name  = "resources.limits.cpu"
      value = "200m"
    },
    {
      name  = "resources.limits.memory"
      value = "500Mi"
    },
    # ===========================================================================
    # Réplicas
    # ===========================================================================
    # 1 réplica em dev, pode aumentar em prod para HA
    {
      name  = "replicaCount"
      value = var.environment == "dev" ? 1 : 2
    },
    # ===========================================================================
    # Service Account
    # ===========================================================================
    # Não criar IRSA annotations (IRSA desabilitado)
    # Autoscaler usa IAM role do node
    {
      name  = "rbac.create"
      value = "true"
    },
    {
      name  = "rbac.serviceAccount.create"
      value = "true"
    },
    {
      name  = "rbac.serviceAccount.name"
      value = "cluster-autoscaler"
    },
  ]
}

# ==============================================================================
# AWS Load Balancer Controller
# ==============================================================================
# O AWS Load Balancer Controller gerencia a integracao entre recursos Kubernetes
# e AWS Elastic Load Balancing (NLB/ALB).
#
# Neste projeto, o controller e responsavel por:
#   - Gerenciar TargetGroupBinding CRDs (registro automatico de pods no NLB)
#   - Sincronizar pod IPs com o Target Group do NLB
#
# NOTA: IRSA está desabilitado devido a SCP. O controller usa IAM role do node
# que já tem ElasticLoadBalancingFullAccess e EC2FullAccess policies anexadas.
# ==============================================================================

resource "helm_release" "aws_load_balancer_controller" {
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  version    = "3.0.0" # Chart version alinhado com controller v3.0.0 (2026-02-03)
  namespace  = "kube-system"

  set = [
    # ===========================================================================
    # Configuração do Cluster
    # ===========================================================================
    {
      name  = "clusterName"
      value = local.eks_cluster_name
    },
    {
      name  = "region"
      value = var.aws_region
    },
    {
      name  = "vpcId"
      value = local.vpc_id
    },
    # ===========================================================================
    # Service Account
    # ===========================================================================
    # Não usar IRSA annotations (IRSA desabilitado)
    # Controller usa IAM role do node
    {
      name  = "serviceAccount.create"
      value = "true"
    },
    {
      name  = "serviceAccount.name"
      value = "aws-load-balancer-controller"
    },
    # ===========================================================================
    # Resources
    # ===========================================================================
    {
      name  = "resources.requests.cpu"
      value = "100m"
    },
    {
      name  = "resources.requests.memory"
      value = "128Mi"
    },
    {
      name  = "resources.limits.cpu"
      value = "200m"
    },
    {
      name  = "resources.limits.memory"
      value = "256Mi"
    },
    # ===========================================================================
    # Réplicas
    # ===========================================================================
    # 2 réplicas para alta disponibilidade
    {
      name  = "replicaCount"
      value = 2
    },
  ]
}

