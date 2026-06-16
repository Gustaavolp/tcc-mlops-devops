# -----------------------------------------------------------------------------
# MLflow Tracking Server Module
# -----------------------------------------------------------------------------
#
# Este módulo cria um MLflow Tracking Server gerenciado pela AWS SageMaker.
#
# Recursos criados:
# - MLflow Tracking Server (AWS SageMaker managed)
# - S3 Bucket para artifacts (encriptado automaticamente pela AWS com SSE-S3)
# - IAM Role com permissões completas
# - CloudWatch Log Group
#
# Referências:
# - https://docs.aws.amazon.com/sagemaker/latest/dg/mlflow.html
# - https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sagemaker_mlflow_tracking_server
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# S3 Bucket para Artifacts
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "artifacts" {
  bucket = var.artifact_bucket_name

  tags = merge(var.tags, {
    Name        = var.artifact_bucket_name
    Environment = var.environment
    Component   = "MLflow-Artifacts"
    Purpose     = "Store MLflow experiment artifacts"
  })
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

# -----------------------------------------------------------------------------
# IAM Role para MLflow Execution
# -----------------------------------------------------------------------------

# IAM Role
resource "aws_iam_role" "execution" {
  name               = var.execution_role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  # Ignorar tags (SSO não tem permissão iam:TagRole)
  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

# Trust Policy (assume role)
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type = "Service"
      identifiers = [
        "sagemaker.amazonaws.com"
      ]
    }

    actions = [
      "sts:AssumeRole"
    ]
  }
}

# -----------------------------------------------------------------------------
# AWS Managed Policy Attachments
# -----------------------------------------------------------------------------
# Usando AWS Managed Policies em vez de custom policies
# Essas policies cobrem as permissões necessárias para MLflow

resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

resource "aws_iam_role_policy_attachment" "firehose_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonKinesisFirehoseFullAccess"
}

# -----------------------------------------------------------------------------
# IAM Policy: Bedrock Full Access (para InvokeModel em foundation models)
# -----------------------------------------------------------------------------
# Necessário para chamar modelos Bedrock a partir do SageMaker Studio
# Ex: bedrock:InvokeModel em foundation-model/openai.gpt-oss-safeguard-120b
# -----------------------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "bedrock_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

# -----------------------------------------------------------------------------
# Policy: SQS Full Access (AWS Managed)
# -----------------------------------------------------------------------------
# Acesso SQS para MLflow execution role

resource "aws_iam_role_policy_attachment" "sqs_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

# -----------------------------------------------------------------------------
# Policy: CodeCommit Power User (AWS Managed)
# -----------------------------------------------------------------------------
# Git no Studio (user profile usa esta role)

resource "aws_iam_role_policy_attachment" "codecommit_power_user" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCodeCommitPowerUser"
}

# -----------------------------------------------------------------------------
# Policy: DynamoDB Full Access (AWS Managed)
# -----------------------------------------------------------------------------
# Acesso DynamoDB para MLflow execution role

resource "aws_iam_role_policy_attachment" "dynamodb_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# -----------------------------------------------------------------------------
# Policy: SageMaker Studio Project Role ML Policy (AWS Managed)
# -----------------------------------------------------------------------------
# Permite uso de Projetos ML no SageMaker Studio

resource "aws_iam_role_policy_attachment" "studio_project_ml_policy" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/SageMakerStudioProjectRoleMachineLearningPolicy"
}

# -----------------------------------------------------------------------------
# Policy: SageMaker MLflow Full Access (Inline)
# -----------------------------------------------------------------------------
# Permite operacoes sagemaker-mlflow:* para o MLflow SDK

resource "aws_iam_role_policy" "sagemaker_mlflow_full_access" {
  name = "SageMakerMLflowFullAccess"
  role = aws_iam_role.execution.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "sagemaker-mlflow:*"
        Resource = "*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# CloudWatch Log Group
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "mlflow" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = var.log_group_name
    Environment = var.environment
    Component   = "MLflow"
  })
}

# -----------------------------------------------------------------------------
# MLflow Tracking Server
# -----------------------------------------------------------------------------

resource "aws_sagemaker_mlflow_tracking_server" "main" {
  tracking_server_name = var.tracking_server_name
  role_arn             = aws_iam_role.execution.arn
  artifact_store_uri   = "s3://${aws_s3_bucket.artifacts.id}"

  # Tamanho do servidor (Small, Medium, Large)
  tracking_server_size = var.tracking_server_size

  # Versão do MLflow
  mlflow_version = var.mlflow_version

  # Janela de manutenção semanal (formato: ddd:hh24:mi)
  weekly_maintenance_window_start = var.weekly_maintenance_window_start

  tags = merge(var.tags, {
    Name        = var.tracking_server_name
    Environment = var.environment
    Component   = "MLflow-TrackingServer"
    Version     = var.mlflow_version
  })

  depends_on = [
    aws_iam_role_policy_attachment.sagemaker_full_access,
    aws_iam_role_policy_attachment.s3_full_access,
    aws_iam_role_policy_attachment.cloudwatch_logs_full_access,
    aws_cloudwatch_log_group.mlflow
  ]
}
