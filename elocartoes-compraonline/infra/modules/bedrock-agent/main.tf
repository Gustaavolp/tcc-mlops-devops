# -----------------------------------------------------------------------------
# Bedrock Agent Module
# -----------------------------------------------------------------------------
# IAM Role para Bedrock Agents com acesso ao Athena para consultas SQL.
# Usado para agentes de IA que consultam dados no Data Lake via Athena.
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.id
}

# -----------------------------------------------------------------------------
# IAM Role - Bedrock Agent
# -----------------------------------------------------------------------------

resource "aws_iam_role" "bedrock_agent" {
  name        = "${var.project_name}-bedrock-agent-${var.environment}"
  description = "Bedrock Agent Role para agentes com acesso ao Athena"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = local.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock:${local.region}:${local.account_id}:agent/*"
          }
        }
      }
    ]
  })

  # NOTA: Tags em IAM Roles removidas devido a SCP que bloqueia iam:TagRole
  # Quando o SCP for ajustado, descomentar: tags = var.tags
}

# Athena - acesso para consultas SQL
resource "aws_iam_role_policy_attachment" "athena" {
  role       = aws_iam_role.bedrock_agent.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonAthenaFullAccess"
}

# S3 - acesso aos buckets do Data Lake
resource "aws_iam_role_policy_attachment" "s3" {
  role       = aws_iam_role.bedrock_agent.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

# Bedrock - acesso aos modelos de IA
resource "aws_iam_role_policy_attachment" "bedrock" {
  role       = aws_iam_role.bedrock_agent.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
}

# Lambda - invocar funcoes auxiliares
resource "aws_iam_role_policy_attachment" "lambda" {
  role       = aws_iam_role.bedrock_agent.name
  policy_arn = "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
}
