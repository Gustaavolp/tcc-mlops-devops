# ==============================================================================
# EKS Pod Identity - IAM Roles (Least-Privilege)
# ==============================================================================
# Roles individuais para cada workload do cluster EKS, substituindo o uso
# de Node IAM Role (broad permissions) por credenciais granulares via
# EKS Pod Identity Agent.
#
# Pre-requisito: addon eks-pod-identity-agent instalado no cluster.
#
# SCP Workarounds aplicados:
#   - Sem tags nas roles (iam:TagRole bloqueado)
#   - Inline policies em vez de custom managed policies (iam:CreatePolicy limitado)
#   - Nomes seguem padrao elo-fraud-* (compatibilidade CodeBuild)
#
# Roles criadas:
#   1. elo-fraud-inference-pod-role-dev    (DynamoDB, SQS, SageMaker MLflow, S3)
#   2. elo-fraud-process-pod-role-dev      (SQS, DynamoDB, Firehose, CloudWatch)
#   3. elo-fraud-lb-controller-role-dev    (ELB, EC2)
#   4. elo-fraud-autoscaler-role-dev       (AutoScaling, EC2, EKS)
#   5. elo-fraud-keda-operator-role-dev    (SQS metrics)
# ==============================================================================

# ==============================================================================
# Locals - Resource ARNs para scoping das IAM policies
# ==============================================================================

locals {
  # Cluster name (para Pod Identity Associations - task futura)
  pod_identity_cluster_name = module.eks.cluster_name

  # ARNs diretos dos modulos na mesma stack
  dynamodb_table_arn  = module.dynamodb.table_arn
  sqs_queue_arn       = module.sqs.queue_arn
  firehose_stream_arn = module.firehose_inference.delivery_stream_arn

  # ARNs pattern-based para recursos cross-stack (MLOps)
  mlflow_artifact_bucket_arn = "arn:aws:s3:::${var.project_name}-mlflow-artifacts-${var.environment}-${var.aws_account_id}"
  sagemaker_bucket_arn       = "arn:aws:s3:::sagemaker-${var.aws_region}-${var.aws_account_id}"
}

# ==============================================================================
# Trust Policy (compartilhada por todas as roles)
# ==============================================================================
# EKS Pod Identity usa pods.eks.amazonaws.com como principal.
# sts:TagSession e obrigatorio para propagacao de session tags.
# ==============================================================================

data "aws_iam_policy_document" "pod_identity_trust" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole",
      "sts:TagSession",
    ]
  }
}

# ==============================================================================
# 1. Inference Pod Role
# ==============================================================================
# Servico: FastAPI (Python 3.12), porta 8000
# Namespace: fraud-detection | ServiceAccount: inference-service
#
# AWS APIs chamadas:
#   - DynamoDB Query (historico de transacoes para feature enrichment)
#   - SQS SendMessage (publica payload enriquecido na fila FIFO)
#   - SageMaker MLflow (carrega modelo XGBoost do Model Registry)
#   - S3 GetObject (download de artefatos de modelo via MLflow)
# ==============================================================================

resource "aws_iam_role" "inference_pod" {
  name               = "${var.project_name}-inference-pod-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_trust.json
}

# --- DynamoDB: Query na tabela de transacoes recentes ---
resource "aws_iam_role_policy" "inference_dynamodb" {
  name = "DynamoDBQuery"
  role = aws_iam_role.inference_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBQueryTable"
        Effect = "Allow"
        Action = ["dynamodb:Query"]
        Resource = [
          local.dynamodb_table_arn,
          "${local.dynamodb_table_arn}/index/*"
        ]
      }
    ]
  })
}

# --- SQS: Enviar mensagens para fila de resultados ---
resource "aws_iam_role_policy" "inference_sqs" {
  name = "SQSSend"
  role = aws_iam_role.inference_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SQSSendMessage"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = local.sqs_queue_arn
      }
    ]
  })
}

# --- SageMaker MLflow: Acesso ao Tracking Server e Model Registry ---
resource "aws_iam_role_policy" "inference_sagemaker_mlflow" {
  name = "SageMakerMLflow"
  role = aws_iam_role.inference_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SageMakerMLflowAccess"
        Effect = "Allow"
        Action = [
          "sagemaker:*",
          "sagemaker-mlflow:*",
        ]
        Resource = "*"
      }
    ]
  })
}

# --- S3: Leitura de artefatos de modelo (MLflow + SageMaker buckets) ---
resource "aws_iam_role_policy" "inference_s3_model_artifacts" {
  name = "S3ModelArtifacts"
  role = aws_iam_role.inference_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "S3ReadModelArtifacts"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = [
          local.mlflow_artifact_bucket_arn,
          "${local.mlflow_artifact_bucket_arn}/*",
          local.sagemaker_bucket_arn,
          "${local.sagemaker_bucket_arn}/*",
        ]
      }
    ]
  })
}

# ==============================================================================
# 2. Process Pod Role
# ==============================================================================
# Servico: SQS Worker (Python 3.9), sem HTTP endpoint
# Namespace: fraud-detection | ServiceAccount: process-service
#
# AWS APIs chamadas:
#   - SQS ReceiveMessage/DeleteMessage (consome fila FIFO)
#   - DynamoDB Query/PutItem/UpdateItem/DeleteItem (CRUD transacoes)
#   - Firehose PutRecord/PutRecordBatch (streaming para S3 data lake)
#   - CloudWatch PutMetricData (metricas customizadas)
# ==============================================================================

resource "aws_iam_role" "process_pod" {
  name               = "${var.project_name}-process-pod-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_trust.json
}

# --- SQS: Consumir mensagens da fila de resultados ---
resource "aws_iam_role_policy" "process_sqs" {
  name = "SQSConsumer"
  role = aws_iam_role.process_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SQSConsumeMessages"
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
        ]
        Resource = local.sqs_queue_arn
      }
    ]
  })
}

# --- DynamoDB: CRUD na tabela de transacoes recentes ---
resource "aws_iam_role_policy" "process_dynamodb" {
  name = "DynamoDBReadWrite"
  role = aws_iam_role.process_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "DynamoDBCRUD"
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
        ]
        Resource = [
          local.dynamodb_table_arn,
          "${local.dynamodb_table_arn}/index/*"
        ]
      }
    ]
  })
}

# --- Firehose: Streaming de inference logs para S3 ---
resource "aws_iam_role_policy" "process_firehose" {
  name = "FirehosePut"
  role = aws_iam_role.process_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "FirehosePutRecord"
        Effect = "Allow"
        Action = [
          "firehose:PutRecord",
          "firehose:PutRecordBatch",
        ]
        Resource = local.firehose_stream_arn
      }
    ]
  })
}

# --- CloudWatch: Publicar metricas customizadas (DynamoSaved, Success) ---
resource "aws_iam_role_policy" "process_cloudwatch" {
  name = "CloudWatchMetrics"
  role = aws_iam_role.process_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "CloudWatchPutMetrics"
        Effect   = "Allow"
        Action   = ["cloudwatch:PutMetricData"]
        Resource = "*"
      }
    ]
  })
}

# ==============================================================================
# 3. AWS Load Balancer Controller Role
# ==============================================================================
# Addon: aws-load-balancer-controller (Helm, kube-system)
# Namespace: kube-system | ServiceAccount: aws-load-balancer-controller
#
# Responsavel por:
#   - Gerenciar TargetGroupBinding CRDs (registro de pods no NLB)
#   - Sincronizar pod IPs com Target Group do NLB
#
# NOTA: ElasticLoadBalancingFullAccess mantida como managed policy pois
# o controller requer um conjunto amplo de ELB actions. A melhoria aqui
# e que essa policy agora so esta disponivel para o controller, nao todos os pods.
# ==============================================================================

resource "aws_iam_role" "lb_controller_pod" {
  name               = "${var.project_name}-lb-controller-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_trust.json
}

# Managed policy: ELB Full Access (necessaria para o controller)
resource "aws_iam_role_policy_attachment" "lb_controller_elb" {
  role       = aws_iam_role.lb_controller_pod.name
  policy_arn = "arn:aws:iam::aws:policy/ElasticLoadBalancingFullAccess"
}

# --- EC2: Permissoes para gerenciamento de ENIs e Security Groups ---
resource "aws_iam_role_policy" "lb_controller_ec2" {
  name = "EC2ForLBController"
  role = aws_iam_role.lb_controller_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EC2DescribeForLBController"
        Effect = "Allow"
        Action = [
          "ec2:DescribeAccountAttributes",
          "ec2:DescribeAddresses",
          "ec2:DescribeAvailabilityZones",
          "ec2:DescribeCoipPools",
          "ec2:DescribeInstances",
          "ec2:DescribeInternetGateways",
          "ec2:DescribeNetworkInterfaces",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeSubnets",
          "ec2:DescribeTags",
          "ec2:DescribeVpcs",
          "ec2:DescribeVpcPeeringConnections",
          "ec2:GetCoipPoolUsage",
        ]
        Resource = "*"
      },
      {
        Sid    = "EC2ManageForLBController"
        Effect = "Allow"
        Action = [
          "ec2:CreateSecurityGroup",
          "ec2:DeleteSecurityGroup",
          "ec2:AuthorizeSecurityGroupIngress",
          "ec2:RevokeSecurityGroupIngress",
          "ec2:CreateTags",
          "ec2:DeleteTags",
        ]
        Resource = "*"
      }
    ]
  })
}

# ==============================================================================
# 4. Cluster Autoscaler Role
# ==============================================================================
# Addon: cluster-autoscaler (Helm, kube-system)
# Namespace: kube-system | ServiceAccount: cluster-autoscaler
#
# Responsavel por:
#   - Escalar nodes para cima quando pods nao cabem nos nodes existentes
#   - Escalar nodes para baixo quando nodes estao subutilizados
# ==============================================================================

resource "aws_iam_role" "autoscaler_pod" {
  name               = "${var.project_name}-autoscaler-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_trust.json
}

resource "aws_iam_role_policy" "autoscaler" {
  name = "ClusterAutoscaler"
  role = aws_iam_role.autoscaler_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AutoScalingReadWrite"
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups",
          "autoscaling:DescribeAutoScalingInstances",
          "autoscaling:DescribeLaunchConfigurations",
          "autoscaling:DescribeScalingActivities",
          "autoscaling:DescribeTags",
          "autoscaling:SetDesiredCapacity",
          "autoscaling:TerminateInstanceInAutoScalingGroup",
        ]
        Resource = "*"
      },
      {
        Sid    = "EC2DescribeForAutoscaler"
        Effect = "Allow"
        Action = [
          "ec2:DescribeImages",
          "ec2:DescribeInstanceTypes",
          "ec2:DescribeLaunchTemplateVersions",
          "ec2:GetInstanceTypesFromInstanceRequirements",
        ]
        Resource = "*"
      },
      {
        Sid      = "EKSDescribeNodegroup"
        Effect   = "Allow"
        Action   = ["eks:DescribeNodegroup"]
        Resource = "*"
      }
    ]
  })
}

# ==============================================================================
# 5. KEDA Operator Role
# ==============================================================================
# Addon: keda (Helm, namespace keda)
# Namespace: keda | ServiceAccount: keda-operator
#
# Responsavel por:
#   - Ler metricas da fila SQS para decidir scaling do Process worker
#   - Usado pelo ScaledObject em k8s/{env}/keda/process-scaledobject.yaml
# ==============================================================================

resource "aws_iam_role" "keda_operator_pod" {
  name               = "${var.project_name}-keda-operator-role-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_trust.json
}

resource "aws_iam_role_policy" "keda_sqs" {
  name = "SQSMetricsForScaling"
  role = aws_iam_role.keda_operator_pod.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SQSGetQueueMetrics"
        Effect = "Allow"
        Action = [
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
        ]
        Resource = local.sqs_queue_arn
      }
    ]
  })
}

# ==============================================================================
# Pod Identity Associations
# ==============================================================================
# Associa cada ServiceAccount K8s a sua respectiva IAM Role via EKS API.
# Mecanismo server-side: NAO requer annotations nos ServiceAccounts.
#
# IMPORTANTE: Apos terraform apply, reiniciar pods para o agent injetar
# as env vars de credenciais:
#   kubectl rollout restart deployment/inference -n fraud-detection
#   kubectl rollout restart deployment/process -n fraud-detection
#   kubectl rollout restart deployment/aws-load-balancer-controller -n kube-system
#   kubectl rollout restart deployment/cluster-autoscaler -n kube-system
#   kubectl rollout restart deployment/keda-operator -n keda
# ==============================================================================

# --- 1. Inference: fraud-detection/inference-service ---
resource "aws_eks_pod_identity_association" "inference" {
  cluster_name    = local.pod_identity_cluster_name
  namespace       = "fraud-detection"
  service_account = "inference-service"
  role_arn        = aws_iam_role.inference_pod.arn
}

# --- 2. Process: fraud-detection/process-service ---
resource "aws_eks_pod_identity_association" "process" {
  cluster_name    = local.pod_identity_cluster_name
  namespace       = "fraud-detection"
  service_account = "process-service"
  role_arn        = aws_iam_role.process_pod.arn
}

# --- 3. AWS LB Controller: kube-system/aws-load-balancer-controller ---
resource "aws_eks_pod_identity_association" "lb_controller" {
  cluster_name    = local.pod_identity_cluster_name
  namespace       = "kube-system"
  service_account = "aws-load-balancer-controller"
  role_arn        = aws_iam_role.lb_controller_pod.arn
}

# --- 4. Cluster Autoscaler: kube-system/cluster-autoscaler ---
resource "aws_eks_pod_identity_association" "autoscaler" {
  cluster_name    = local.pod_identity_cluster_name
  namespace       = "kube-system"
  service_account = "cluster-autoscaler"
  role_arn        = aws_iam_role.autoscaler_pod.arn
}

# --- 5. KEDA Operator: keda/keda-operator ---
# identityOwner: operator no ScaledObject = KEDA operator faz as chamadas AWS
resource "aws_eks_pod_identity_association" "keda_operator" {
  cluster_name    = local.pod_identity_cluster_name
  namespace       = "keda"
  service_account = "keda-operator"
  role_arn        = aws_iam_role.keda_operator_pod.arn
}
