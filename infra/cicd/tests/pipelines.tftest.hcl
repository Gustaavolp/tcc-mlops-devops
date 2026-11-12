# Testes da stack de CI/CD (terraform test), executados offline com provider
# simulado e saídas das stacks platform injetadas. Rodam na etapa de validação
# do pipeline de infraestrutura (pipelines/scripts/tf_stacks.sh validate).

mock_provider "aws" {}

mock_provider "aws" {
  alias = "staging"
}

override_data {
  target = data.aws_caller_identity.current
  values = {
    account_id = "123456789012"
  }
}

override_data {
  target = data.terraform_remote_state.platform["dev"]
  values = {
    outputs = {
      eks_cluster_name             = "elo-fraud-eks-dev"
      api_health_endpoint_url      = "https://dev.example.com/v1/health"
      ecr_inference_repository_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-inference-dev"
      ecr_process_repository_url   = "123456789012.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-process-dev"
      ecr_model_repository_url     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/elo-fraud-model-dev"
      ecr_etl_delta_filter_url     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/etl-delta-filter-dev"
      ecr_training_launcher_url    = "123456789012.dkr.ecr.us-east-1.amazonaws.com/training-launcher-dev"
      ecr_register_best_model_url  = "123456789012.dkr.ecr.us-east-1.amazonaws.com/best-model-register-dev"
    }
  }
}

override_data {
  target = data.terraform_remote_state.platform["staging"]
  values = {
    outputs = {
      eks_cluster_name             = "elo-fraud-eks-staging"
      api_health_endpoint_url      = "https://staging.example.com/v1/health"
      ecr_inference_repository_url = "123456789012.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-inference-staging"
      ecr_process_repository_url   = "123456789012.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-process-staging"
      ecr_model_repository_url     = "123456789012.dkr.ecr.sa-east-1.amazonaws.com/elo-fraud-model-staging"
      ecr_etl_delta_filter_url     = "123456789012.dkr.ecr.sa-east-1.amazonaws.com/etl-delta-filter-staging"
      ecr_training_launcher_url    = "123456789012.dkr.ecr.sa-east-1.amazonaws.com/training-launcher-staging"
      ecr_register_best_model_url  = "123456789012.dkr.ecr.sa-east-1.amazonaws.com/best-model-register-staging"
    }
  }
}

variables {
  approval_sns_topic_arn = null
}

run "um_pipeline_por_artefato_mais_infra" {
  command = plan

  assert {
    condition     = toset(keys(aws_codepipeline.app)) == toset(["inference", "process", "training-image", "etl-delta-filter", "training-launcher", "register-best-model"])
    error_message = "Deve existir um pipeline por artefato conteinerizado (6)."
  }
  assert {
    condition     = length(aws_cloudwatch_event_rule.push) == 7
    error_message = "Cada um dos 7 pipelines precisa de uma regra de push no EventBridge."
  }
}

run "estagios_do_pipeline_de_aplicacao" {
  command = plan

  assert {
    condition     = [for s in aws_codepipeline.app["inference"].stage : s.name] == ["Source", "Build", "DeployDev", "ApproveStaging", "DeployStaging"]
    error_message = "Ordem esperada: Source -> Build -> DeployDev -> aprovação -> DeployStaging."
  }
  assert {
    condition     = [for a in aws_codepipeline.app["inference"].stage[1].action : a.name] == ["DetectChanges", "LintTestBuildPush"]
    error_message = "O build deve detectar mudanças antes de construir."
  }
  assert {
    condition     = aws_codepipeline.app["inference"].stage[0].action[0].configuration.OutputArtifactFormat == "CODEBUILD_CLONE_REF"
    error_message = "A detecção de mudanças precisa do clone git completo."
  }
}

run "estagios_do_pipeline_de_infraestrutura" {
  command = plan

  assert {
    condition     = [for s in aws_codepipeline.infra.stage : s.name] == ["Source", "Validate", "PlanDev", "ApproveDev", "ApplyDev", "PlanStaging", "ApproveStaging", "ApplyStaging"]
    error_message = "Toda aplicação de Terraform deve ser precedida de plano e aprovação, e Staging só depois de DEV."
  }
  assert {
    condition     = aws_codepipeline.infra.execution_mode == "QUEUED"
    error_message = "O pipeline de infraestrutura não pode substituir execuções em andamento."
  }
}

run "variaveis_de_implantacao_eks" {
  command = plan

  assert {
    condition     = local.deploy_vars["inference"]["dev"]["MANIFEST_DIRS"] == "k8s/dev/inference"
    error_message = "Manifestos de dev devem vir de k8s/dev."
  }
  assert {
    condition     = local.deploy_vars["process"]["staging"]["MANIFEST_DIRS"] == "k8s/staging/process k8s/staging/keda"
    error_message = "O process deve aplicar também o ScaledObject do KEDA."
  }
  assert {
    condition     = local.deploy_vars["inference"]["staging"]["EKS_CLUSTER"] == "elo-fraud-eks-staging"
    error_message = "Cluster de staging incorreto."
  }
  assert {
    condition     = local.deploy_vars["inference"]["dev"]["IMAGE_TAG"] == "#{SourceVariables.CommitId}"
    error_message = "A tag da imagem deve ser o commit."
  }
}

run "promocao_para_staging_usa_a_mesma_imagem" {
  command = plan

  assert {
    condition = {
      for e in jsondecode(aws_codepipeline.app["etl-delta-filter"].stage[4].action[0].configuration.EnvironmentVariables) : e.name => e.value
      } == {
      ARTIFACT           = "etl-delta-filter"
      TARGET_ENV         = "staging"
      DEPLOY_KIND        = "lambda"
      TARGET_REPO_URL    = "123456789012.dkr.ecr.sa-east-1.amazonaws.com/etl-delta-filter-staging"
      SOURCE_REPO_URL    = "123456789012.dkr.ecr.us-east-1.amazonaws.com/etl-delta-filter-dev"
      IMAGE_TAG          = "#{SourceVariables.CommitId}"
      HEALTH_URL         = "https://staging.example.com/v1/health"
      LAMBDA_FUNCTION    = "elo-fraud-etl-delta-filter-staging"
      STATE_PARAM_PREFIX = "/elo-fraud/cicd"
      RECORD_COMMIT      = "1"
    }
    error_message = "Deploy de staging de Lambda: promoção a partir do ECR de dev, sem variáveis de EKS, registrando o commit."
  }
}

run "imagem_de_treino_aponta_parametro_ssm" {
  command = plan

  assert {
    condition     = local.deploy_vars["training-image"]["dev"]["TRAINING_IMAGE_PARAM"] == "/elo-fraud/dev/training-image"
    error_message = "A imagem de treino é implantada pelo parâmetro SSM lido pela training-launcher."
  }
  assert {
    condition     = !contains(keys(local.deploy_vars["training-image"]["dev"]), "EKS_CLUSTER")
    error_message = "Artefatos que não são EKS não recebem variáveis de EKS."
  }
}

run "rollout_do_modelo_por_ambiente" {
  command = plan

  assert {
    condition     = jsondecode(aws_cloudwatch_event_rule.model_registered_staging.event_pattern).detail.environment == ["staging"]
    error_message = "O rollout de staging só deve reagir a eventos de staging."
  }
  assert {
    condition     = { for v in aws_codebuild_project.model_rollout_dev.environment[0].environment_variable : v.name => v.value }["K8S_DEPLOYMENT"] == "inference"
    error_message = "O rollout reinicia o Deployment de inferência."
  }
}

run "codebuild_de_build_e_privilegiado_e_demais_nao" {
  command = plan

  assert {
    condition     = aws_codebuild_project.pipeline["app-build"].environment[0].privileged_mode
    error_message = "docker build exige modo privilegiado."
  }
  assert {
    condition     = !aws_codebuild_project.pipeline["app-deploy"].environment[0].privileged_mode
    error_message = "Deploy não precisa de modo privilegiado."
  }
}
