# ==============================================================================
# Roles IAM do CI/CD — uma por responsabilidade, com permissões mínimas
# ==============================================================================

locals {
  pipeline_arn_pattern = "arn:aws:codepipeline:${local.dev_region}:${local.account_id}:${var.project_name}-*"

  logs_statement = {
    Effect   = "Allow"
    Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    Resource = "arn:aws:logs:*:${local.account_id}:log-group:/aws/codebuild/${var.project_name}-*"
  }
  artifacts_statement = {
    Effect   = "Allow"
    Action   = ["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject", "s3:GetBucketLocation", "s3:ListBucket"]
    Resource = [aws_s3_bucket.artifacts.arn, "${aws_s3_bucket.artifacts.arn}/*"]
  }
  git_pull_statement = {
    Effect   = "Allow"
    Action   = ["codecommit:GitPull"]
    Resource = local.repository_arn
  }
}

locals {
  assume_role_policy = {
    for svc in ["codepipeline", "codebuild", "events"] : svc => jsonencode({
      Version = "2012-10-17"
      Statement = [{
        Effect    = "Allow"
        Action    = "sts:AssumeRole"
        Principal = { Service = "${svc}.amazonaws.com" }
      }]
    })
  }
}

# ------------------------------------------------------------------ CodePipeline
resource "aws_iam_role" "codepipeline" {
  name               = "${var.project_name}-cicd-codepipeline"
  assume_role_policy = local.assume_role_policy["codepipeline"]
}

resource "aws_iam_role_policy" "codepipeline" {
  name = "pipeline"
  role = aws_iam_role.codepipeline.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      local.artifacts_statement,
      {
        Effect = "Allow"
        Action = ["codecommit:GetBranch", "codecommit:GetCommit", "codecommit:GetRepository",
        "codecommit:UploadArchive", "codecommit:GetUploadArchiveStatus", "codecommit:CancelUploadArchive"]
        Resource = local.repository_arn
      },
      {
        Effect   = "Allow"
        Action   = ["codebuild:StartBuild", "codebuild:BatchGetBuilds", "codebuild:StopBuild"]
        Resource = [for p in local.pipeline_codebuild_projects : p.arn]
      },
      ], var.approval_sns_topic_arn == null ? [] : [{
        Effect   = "Allow"
        Action   = ["sns:Publish"]
        Resource = var.approval_sns_topic_arn
    }])
  })
}

# ------------------------------------------- CodeBuild: aplicação (build/deploy)
resource "aws_iam_role" "codebuild_app" {
  name               = "${var.project_name}-cicd-app"
  assume_role_policy = local.assume_role_policy["codebuild"]
}

resource "aws_iam_role_policy" "codebuild_app" {
  name = "app"
  role = aws_iam_role.codebuild_app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      local.logs_statement,
      local.artifacts_statement,
      local.git_pull_statement,
      { # detecção de mudanças: estado por artefato e encerramento da execução
        Effect   = "Allow"
        Action   = ["ssm:GetParameter", "ssm:PutParameter"]
        Resource = "arn:aws:ssm:${local.dev_region}:${local.account_id}:parameter${local.state_param_prefix}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["codepipeline:StopPipelineExecution"]
        Resource = local.pipeline_arn_pattern
      },
      { # build e promoção de imagens
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["ecr:BatchCheckLayerAvailability", "ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer",
          "ecr:DescribeImages", "ecr:InitiateLayerUpload", "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload", "ecr:PutImage"]
        Resource = local.ecr_repository_arns
      },
      { # implantação: EKS (RBAC via grupo cicd-deployers), Lambda e imagem de treino
        Effect   = "Allow"
        Action   = ["eks:DescribeCluster"]
        Resource = local.eks_cluster_arns
      },
      {
        Effect   = "Allow"
        Action   = ["lambda:UpdateFunctionCode", "lambda:GetFunction", "lambda:GetFunctionConfiguration"]
        Resource = local.lambda_function_arns
      },
      {
        Effect   = "Allow"
        Action   = ["ssm:GetParameter", "ssm:PutParameter"]
        Resource = local.training_image_param_arns
      },
    ]
  })
}

# --------------------------------------------- CodeBuild: infraestrutura (Terraform)
# O Terraform cria e altera recursos de praticamente todos os serviços da
# plataforma; por isso usa AdministratorAccess, mitigado por aprovação manual
# antes de todo apply e por logs de auditoria (CloudTrail).
resource "aws_iam_role" "codebuild_infra" {
  name               = "${var.project_name}-cicd-infra"
  assume_role_policy = local.assume_role_policy["codebuild"]
}

resource "aws_iam_role_policy_attachment" "codebuild_infra_admin" {
  role       = aws_iam_role.codebuild_infra.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}

# ------------------------------------------------- CodeBuild: rollout do modelo
resource "aws_iam_role" "model_rollout" {
  name               = "${var.project_name}-cicd-model-rollout"
  assume_role_policy = local.assume_role_policy["codebuild"]
}

resource "aws_iam_role_policy" "model_rollout" {
  name = "rollout"
  role = aws_iam_role.model_rollout.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      local.logs_statement,
      {
        Effect   = "Allow"
        Action   = ["eks:DescribeCluster"]
        Resource = local.eks_cluster_arns
      },
    ]
  })
}

# ------------------------------------------------------------------ EventBridge
resource "aws_iam_role" "events" {
  name               = "${var.project_name}-cicd-events"
  assume_role_policy = local.assume_role_policy["events"]
}

resource "aws_iam_role_policy" "events" {
  name = "start"
  role = aws_iam_role.events.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["codepipeline:StartPipelineExecution"]
        Resource = local.pipeline_arn_pattern
      },
      {
        Effect   = "Allow"
        Action   = ["codebuild:StartBuild"]
        Resource = [aws_codebuild_project.model_rollout_dev.arn, aws_codebuild_project.model_rollout_staging.arn]
      },
    ]
  })
}
