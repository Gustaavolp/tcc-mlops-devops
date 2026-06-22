# =============================================================================
# KEDA - Kubernetes Event-driven Autoscaling (Helm)
# =============================================================================
# KEDA permite autoscaling baseado em eventos externos como:
#   - Profundidade de filas SQS
#   - Metricas customizadas
#   - Cron schedules
#
# Usado pelo Process worker para escalar baseado em mensagens na fila SQS.
# O ScaledObject e gerenciado via kubectl (k8s/staging/keda/process-scaledobject.yaml).
# =============================================================================

resource "helm_release" "keda" {
  name       = "keda"
  repository = "https://kedacore.github.io/charts"
  chart      = "keda"
  version    = "2.18.3" # Atualizado em 2026-02-03
  namespace  = "keda"

  create_namespace = true

  # Evita race condition: o LB Controller registra um mutating webhook que
  # intercepta criacao de Services. Se o KEDA instalar antes dos pods do
  # LB Controller estarem ready, o webhook falha e o KEDA falha junto.
  depends_on = [helm_release.aws_load_balancer_controller]

  set = [
    # ===========================================================================
    # Configuracoes de Recursos
    # ===========================================================================
    # Operator
    {
      name  = "resources.operator.requests.cpu"
      value = "100m"
    },
    {
      name  = "resources.operator.requests.memory"
      value = "128Mi"
    },
    {
      name  = "resources.operator.limits.cpu"
      value = "500m"
    },
    {
      name  = "resources.operator.limits.memory"
      value = "256Mi"
    },
    # Metrics Server
    {
      name  = "resources.metricServer.requests.cpu"
      value = "100m"
    },
    {
      name  = "resources.metricServer.requests.memory"
      value = "128Mi"
    },
    {
      name  = "resources.metricServer.limits.cpu"
      value = "500m"
    },
    {
      name  = "resources.metricServer.limits.memory"
      value = "256Mi"
    },
    # ===========================================================================
    # Replicas - STAGING usa 1 replica (menos recursos)
    # ===========================================================================
    {
      name  = "operator.replicaCount"
      value = 1
    },
    {
      name  = "metricServer.replicaCount"
      value = 1
    },
    # ===========================================================================
    # Logging
    # ===========================================================================
    {
      name  = "logging.operator.level"
      value = "info"
    },
    {
      name  = "logging.metricServer.level"
      value = "0" # 0 = info level
    },
  ]
}
