# -----------------------------------------------------------------------------
# Lambda Module (Container Image Only)
# -----------------------------------------------------------------------------
# Deploy de Lambda functions usando imagens de container ECR.
# Inclui: IAM Role, CloudWatch Logs, S3 Trigger (opcional)
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# IAM Role
# -----------------------------------------------------------------------------

resource "aws_iam_role" "lambda" {
  name        = var.function_name
  description = "IAM Role para Lambda ${var.function_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  # SCP bloqueia iam:TagRole e iam:UpdateRoleDescription
  lifecycle {
    ignore_changes = [tags, tags_all, description]
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "managed_policies" {
  count = length(var.managed_policy_arns)

  role       = aws_iam_role.lambda.name
  policy_arn = var.managed_policy_arns[count.index]
}

resource "aws_iam_role_policy" "inline" {
  count = var.inline_policy_json == null ? 0 : 1

  name   = "${var.function_name}-inline"
  role   = aws_iam_role.lambda.id
  policy = var.inline_policy_json
}

# -----------------------------------------------------------------------------
# CloudWatch Log Group
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name        = "${var.function_name}-logs"
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# Lambda Function (Container Image)
# -----------------------------------------------------------------------------

resource "aws_lambda_function" "container" {
  function_name = var.function_name
  description   = var.description
  role          = aws_iam_role.lambda.arn
  timeout       = var.timeout
  memory_size   = var.memory_size
  package_type  = "Image"

  image_uri = var.image_uri

  environment {
    variables = merge(
      { ENVIRONMENT = var.environment },
      var.environment_variables
    )
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda,
    aws_iam_role_policy_attachment.lambda_basic
  ]

  tags = merge(var.tags, {
    Name        = var.function_name
    Environment = var.environment
  })

  # CI/CD atualiza a imagem Docker - Terraform nao deve reverter
  lifecycle {
    ignore_changes = [image_uri]
  }
}

# -----------------------------------------------------------------------------
# S3 Trigger (Opcional)
# -----------------------------------------------------------------------------
# Permite que um bucket S3 invoque a Lambda quando objetos são criados/modificados
# Suporta filtros por prefixo e sufixo para maior controle
# -----------------------------------------------------------------------------

resource "aws_lambda_permission" "s3_trigger" {
  count = var.enable_s3_trigger ? 1 : 0

  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.container.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.s3_trigger_bucket_name}"
}

resource "aws_s3_bucket_notification" "lambda_trigger" {
  count  = var.enable_s3_trigger ? 1 : 0
  bucket = var.s3_trigger_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.container.arn
    events              = var.s3_trigger_events
    filter_prefix       = var.s3_trigger_filter_prefix
    filter_suffix       = var.s3_trigger_filter_suffix
  }

  depends_on = [aws_lambda_permission.s3_trigger]
}
