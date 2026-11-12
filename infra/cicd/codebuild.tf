# ==============================================================================
# Projetos CodeBuild usados pelas ações dos pipelines
# ==============================================================================
# Os projetos são genéricos: cada ação do CodePipeline informa o artefato e o
# ambiente por variáveis de ambiente. Os buildspecs ficam versionados em
# pipelines/buildspecs/ (e buildspecs/ para o pipeline de IAM).
# ==============================================================================

locals {
  codebuild_projects = {
    detect = {
      description = "Encerra a execução se o artefato não mudou desde o último commit promovido"
      buildspec   = "pipelines/buildspecs/detect-changes.yml"
      role_arn    = aws_iam_role.codebuild_app.arn
      compute     = "BUILD_GENERAL1_SMALL"
      privileged  = false
      timeout     = 10
    }
    record = {
      description = "Registra o commit promovido (base da detecção de mudanças)"
      buildspec   = "pipelines/buildspecs/record-commit.yml"
      role_arn    = aws_iam_role.codebuild_app.arn
      compute     = "BUILD_GENERAL1_SMALL"
      privileged  = false
      timeout     = 10
    }
    app-build = {
      description = "Análise estática, docker build, pytest na imagem e push no ECR (tag = commit)"
      buildspec   = "pipelines/buildspecs/app-build.yml"
      role_arn    = aws_iam_role.codebuild_app.arn
      compute     = "BUILD_GENERAL1_LARGE" # imagem de treino (TensorFlow) é pesada
      privileged  = true                   # docker build
      timeout     = 90
    }
    app-deploy = {
      description = "Promoção da imagem, implantação no ambiente e testes de fumaça"
      buildspec   = "pipelines/buildspecs/app-deploy.yml"
      role_arn    = aws_iam_role.codebuild_app.arn
      compute     = "BUILD_GENERAL1_SMALL"
      privileged  = false
      timeout     = 45
    }
    infra = {
      description = "Terraform: validate, plan e apply das stacks"
      buildspec   = "pipelines/buildspecs/infra.yml"
      role_arn    = aws_iam_role.codebuild_infra.arn
      compute     = "BUILD_GENERAL1_MEDIUM"
      privileged  = false
      timeout     = 120
    }
  }

  pipeline_codebuild_projects = values(aws_codebuild_project.pipeline)
}

resource "aws_cloudwatch_log_group" "codebuild" {
  for_each          = local.codebuild_projects
  name              = "/aws/codebuild/${var.project_name}-cicd-${each.key}"
  retention_in_days = var.log_retention_days
}

resource "aws_codebuild_project" "pipeline" {
  for_each = local.codebuild_projects

  name          = "${var.project_name}-cicd-${each.key}"
  description   = each.value.description
  service_role  = each.value.role_arn
  build_timeout = each.value.timeout

  source {
    type      = "CODEPIPELINE"
    buildspec = each.value.buildspec
  }

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    type            = "LINUX_CONTAINER"
    compute_type    = each.value.compute
    image           = var.codebuild_image
    privileged_mode = each.value.privileged
  }

  logs_config {
    cloudwatch_logs {
      group_name = aws_cloudwatch_log_group.codebuild[each.key].name
    }
  }
}

# ==============================================================================
# Rollout do modelo (um projeto por região; sem código-fonte)
# ==============================================================================
# Acionado pelo EventBridge quando a register-best-model registra uma nova versão
# no ambiente. Executa o rolling restart do Deployment de inferência: os pods
# novos carregam a versão recém-registrada na inicialização.
# ==============================================================================

locals {
  rollout_env_vars = {
    for env, _ in var.environments : env => {
      TARGET_ENV     = env
      EKS_CLUSTER    = local.platform[env].eks_cluster_name
      K8S_NAMESPACE  = var.k8s_namespace
      K8S_DEPLOYMENT = "inference"
      HEALTH_URL     = local.platform[env].api_health_endpoint_url
    }
  }
  rollout_buildspec = file("${path.module}/../../pipelines/buildspecs/model-rollout.yml")
}

resource "aws_cloudwatch_log_group" "model_rollout_dev" {
  name              = "/aws/codebuild/${var.project_name}-cicd-model-rollout-dev"
  retention_in_days = var.log_retention_days
}

resource "aws_codebuild_project" "model_rollout_dev" {
  name          = "${var.project_name}-cicd-model-rollout-dev"
  description   = "Rolling restart da inferência após nova versão do modelo (dev)"
  service_role  = aws_iam_role.model_rollout.arn
  build_timeout = 30

  source {
    type      = "NO_SOURCE"
    buildspec = local.rollout_buildspec
  }

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    type         = "LINUX_CONTAINER"
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = var.codebuild_image

    dynamic "environment_variable" {
      for_each = local.rollout_env_vars["dev"]
      content {
        name  = environment_variable.key
        value = environment_variable.value
      }
    }
  }

  logs_config {
    cloudwatch_logs {
      group_name = aws_cloudwatch_log_group.model_rollout_dev.name
    }
  }
}

resource "aws_cloudwatch_log_group" "model_rollout_staging" {
  provider          = aws.staging
  name              = "/aws/codebuild/${var.project_name}-cicd-model-rollout-staging"
  retention_in_days = var.log_retention_days
}

resource "aws_codebuild_project" "model_rollout_staging" {
  provider      = aws.staging
  name          = "${var.project_name}-cicd-model-rollout-staging"
  description   = "Rolling restart da inferência após nova versão do modelo (staging)"
  service_role  = aws_iam_role.model_rollout.arn
  build_timeout = 30

  source {
    type      = "NO_SOURCE"
    buildspec = local.rollout_buildspec
  }

  artifacts {
    type = "NO_ARTIFACTS"
  }

  environment {
    type         = "LINUX_CONTAINER"
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = var.codebuild_image

    dynamic "environment_variable" {
      for_each = local.rollout_env_vars["staging"]
      content {
        name  = environment_variable.key
        value = environment_variable.value
      }
    }
  }

  logs_config {
    cloudwatch_logs {
      group_name = aws_cloudwatch_log_group.model_rollout_staging.name
    }
  }
}
