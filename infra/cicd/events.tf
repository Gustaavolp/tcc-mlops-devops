# ==============================================================================
# Gatilhos (Amazon EventBridge)
# ==============================================================================

locals {
  pipelines = merge(
    { for a, p in aws_codepipeline.app : "app-${a}" => p.arn },
    { infra = aws_codepipeline.infra.arn },
  )
}

# Push na branch -> todos os pipelines (cada um decide, na etapa DetectChanges,
# se o seu artefato mudou). Uma regra por pipeline: limite de 5 alvos por regra.
resource "aws_cloudwatch_event_rule" "push" {
  for_each = local.pipelines

  name        = "${var.project_name}-cicd-push-${each.key}"
  description = "Push em ${var.repository_name}/${var.branch} dispara ${each.key}"
  event_pattern = jsonencode({
    source        = ["aws.codecommit"]
    "detail-type" = ["CodeCommit Repository State Change"]
    resources     = [local.repository_arn]
    detail = {
      event         = ["referenceCreated", "referenceUpdated"]
      referenceType = ["branch"]
      referenceName = [var.branch]
    }
  })
}

resource "aws_cloudwatch_event_target" "push" {
  for_each = local.pipelines

  rule     = aws_cloudwatch_event_rule.push[each.key].name
  arn      = each.value
  role_arn = aws_iam_role.events.arn
}

# Nova versão registrada pela register-best-model -> rolling restart da
# inferência no MESMO ambiente (o EventBridge é regional).
locals {
  model_event_pattern = {
    for env, _ in var.environments : env => jsonencode({
      source        = ["elo-fraud.mlops"]
      "detail-type" = ["ModelVersionRegistered"]
      detail        = { environment = [env] }
    })
  }
  # Repassa a versão do modelo ao build (aparece nos logs do rollout)
  model_event_input_paths    = { version = "$.detail.version" }
  model_event_input_template = "{\"environmentVariablesOverride\":[{\"name\":\"MODEL_VERSION\",\"value\":<version>,\"type\":\"PLAINTEXT\"}]}"
}

resource "aws_cloudwatch_event_rule" "model_registered_dev" {
  name          = "${var.project_name}-cicd-model-registered-dev"
  description   = "Nova versão do modelo em dev -> rollout da inferência"
  event_pattern = local.model_event_pattern["dev"]
}

resource "aws_cloudwatch_event_target" "model_registered_dev" {
  rule     = aws_cloudwatch_event_rule.model_registered_dev.name
  arn      = aws_codebuild_project.model_rollout_dev.arn
  role_arn = aws_iam_role.events.arn

  input_transformer {
    input_paths    = local.model_event_input_paths
    input_template = local.model_event_input_template
  }
}

resource "aws_cloudwatch_event_rule" "model_registered_staging" {
  provider      = aws.staging
  name          = "${var.project_name}-cicd-model-registered-staging"
  description   = "Nova versão do modelo em staging -> rollout da inferência"
  event_pattern = local.model_event_pattern["staging"]
}

resource "aws_cloudwatch_event_target" "model_registered_staging" {
  provider = aws.staging
  rule     = aws_cloudwatch_event_rule.model_registered_staging.name
  arn      = aws_codebuild_project.model_rollout_staging.arn
  role_arn = aws_iam_role.events.arn

  input_transformer {
    input_paths    = local.model_event_input_paths
    input_template = local.model_event_input_template
  }
}
