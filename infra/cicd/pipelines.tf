# ==============================================================================
# Pipelines (AWS CodePipeline V2)
# ==============================================================================
#   app-<artefato> (6): Source -> Build (detecção, análise estática, docker build,
#                       pytest na imagem, push ECR) -> DeployDev (+ smoke) ->
#                       aprovação manual -> DeployStaging (mesma imagem + smoke)
#   infra:              Source -> Detect -> Validate -> PlanDev -> aprovação ->
#                       ApplyDev -> PlanStaging -> aprovação -> ApplyStaging
# Permissões IAM das workloads são IaC (Pod Identity, stack platform) e mudam
# pelo pipeline de infraestrutura, com plano revisado e aprovação.
# Disparo: regra do EventBridge por pipeline a cada push na branch (events.tf).
# ==============================================================================

locals {
  # Variáveis de ambiente no formato aceito pela ação CodeBuild do CodePipeline
  env_json = {
    for key, vars in merge(
      { for a, cfg in local.artifacts : "app-${a}/detect" => {
        ARTIFACT              = a
        WATCH_PATHS           = join(" ", cfg.watch_paths)
        PIPELINE_NAME         = "${var.project_name}-app-${a}"
        PIPELINE_EXECUTION_ID = "#{codepipeline.PipelineExecutionId}"
        STATE_PARAM_PREFIX    = local.state_param_prefix
      } },
      { for a, cfg in local.artifacts : "app-${a}/build" => {
        ARTIFACT     = a
        CONTEXT_DIR  = cfg.context_dir
        LINT_PATHS   = cfg.lint_paths
        TEST_DIR     = cfg.test_dir
        TEST_WORKDIR = cfg.test_workdir
        TEST_DEPS    = cfg.test_deps
        ECR_REPO_URL = local.platform["dev"][cfg.ecr_output]
        IMAGE_TAG    = local.image_tag
      } },
      { for a, cfg in local.artifacts : "app-${a}/deploy-dev" => local.deploy_vars[a]["dev"] },
      { for a, cfg in local.artifacts : "app-${a}/deploy-staging" => merge(local.deploy_vars[a]["staging"], {
        SOURCE_REPO_URL = local.platform["dev"][cfg.ecr_output] # promoção da MESMA imagem
        RECORD_COMMIT   = "1"
      }) },
      {
        "infra/detect" = {
          ARTIFACT              = "infra"
          WATCH_PATHS           = "infra pipelines ruff.toml"
          PIPELINE_NAME         = "${var.project_name}-infra"
          PIPELINE_EXECUTION_ID = "#{codepipeline.PipelineExecutionId}"
          STATE_PARAM_PREFIX    = local.state_param_prefix
        }
        "infra/validate"      = { TF_ACTION = "validate" }
        "infra/plan-dev"      = { TF_ACTION = "plan", TF_ENV = "dev" }
        "infra/apply-dev"     = { TF_ACTION = "apply", TF_ENV = "dev", PLAN_ARTIFACT = "PlanDev" }
        "infra/plan-staging"  = { TF_ACTION = "plan", TF_ENV = "staging" }
        "infra/apply-staging" = { TF_ACTION = "apply", TF_ENV = "staging", PLAN_ARTIFACT = "PlanStaging" }
        "infra/record"        = { ARTIFACT = "infra", STATE_PARAM_PREFIX = local.state_param_prefix }
      }
    ) : key => jsonencode([for k, v in vars : { name = k, value = v, type = "PLAINTEXT" }])
  }

  source_configuration = {
    RepositoryName       = local.repository_name
    BranchName           = var.branch
    PollForSourceChanges = "false"               # disparo via EventBridge
    OutputArtifactFormat = "CODEBUILD_CLONE_REF" # clone git completo (diff entre commits)
  }

  approval_configuration = {
    for k, v in {
      CustomData      = "Revise os logs da etapa anterior antes de aprovar."
      NotificationArn = var.approval_sns_topic_arn
    } : k => v if v != null
  }

  project = { for k, p in aws_codebuild_project.pipeline : k => p.name }
}

# ------------------------------------------------------------- aplicação (6x)
resource "aws_codepipeline" "app" {
  for_each = local.artifacts

  name           = "${var.project_name}-app-${each.key}"
  role_arn       = aws_iam_role.codepipeline.arn
  pipeline_type  = "V2"
  execution_mode = "SUPERSEDED" # o commit mais recente substitui execuções aguardando aprovação

  artifact_store {
    location = aws_s3_bucket.artifacts.bucket
    type     = "S3"
  }

  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeCommit"
      version          = "1"
      namespace        = "SourceVariables"
      output_artifacts = ["Source"]
      configuration    = local.source_configuration
    }
  }

  stage {
    name = "Build"
    action {
      name            = "DetectChanges"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      run_order       = 1
      input_artifacts = ["Source"]
      configuration = {
        ProjectName          = local.project["detect"]
        EnvironmentVariables = local.env_json["app-${each.key}/detect"]
      }
    }
    action {
      name            = "LintTestBuildPush"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      run_order       = 2
      input_artifacts = ["Source"]
      configuration = {
        ProjectName          = local.project["app-build"]
        EnvironmentVariables = local.env_json["app-${each.key}/build"]
      }
    }
  }

  stage {
    name = "DeployDev"
    action {
      name            = "DeployAndSmokeTest"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["Source"]
      configuration = {
        ProjectName          = local.project["app-deploy"]
        EnvironmentVariables = local.env_json["app-${each.key}/deploy-dev"]
      }
    }
  }

  stage {
    name = "ApproveStaging"
    action {
      name          = "ManualApproval"
      category      = "Approval"
      owner         = "AWS"
      provider      = "Manual"
      version       = "1"
      configuration = local.approval_configuration
    }
  }

  stage {
    name = "DeployStaging"
    action {
      name            = "PromoteDeployAndSmokeTest"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["Source"]
      configuration = {
        ProjectName          = local.project["app-deploy"]
        EnvironmentVariables = local.env_json["app-${each.key}/deploy-staging"]
      }
    }
  }
}

# ------------------------------------------------------------- infraestrutura
resource "aws_codepipeline" "infra" {
  name           = "${var.project_name}-infra"
  role_arn       = aws_iam_role.codepipeline.arn
  pipeline_type  = "V2"
  execution_mode = "QUEUED" # nunca interromper/sobrepor execuções que aplicam Terraform

  artifact_store {
    location = aws_s3_bucket.artifacts.bucket
    type     = "S3"
  }

  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "CodeCommit"
      version          = "1"
      namespace        = "SourceVariables"
      output_artifacts = ["Source"]
      configuration    = local.source_configuration
    }
  }

  stage {
    name = "Validate"
    action {
      name            = "DetectChanges"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      run_order       = 1
      input_artifacts = ["Source"]
      configuration = {
        ProjectName          = local.project["detect"]
        EnvironmentVariables = local.env_json["infra/detect"]
      }
    }
    action {
      name            = "FmtAndValidate"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      run_order       = 2
      input_artifacts = ["Source"]
      configuration = {
        ProjectName          = local.project["infra"]
        EnvironmentVariables = local.env_json["infra/validate"]
      }
    }
  }

  stage {
    name = "PlanDev"
    action {
      name             = "Plan"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["Source"]
      output_artifacts = ["PlanDev"]
      configuration = {
        ProjectName          = local.project["infra"]
        EnvironmentVariables = local.env_json["infra/plan-dev"]
      }
    }
  }

  stage {
    name = "ApproveDev"
    action {
      name          = "ManualApproval"
      category      = "Approval"
      owner         = "AWS"
      provider      = "Manual"
      version       = "1"
      configuration = local.approval_configuration
    }
  }

  stage {
    name = "ApplyDev"
    action {
      name            = "Apply"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      input_artifacts = ["Source", "PlanDev"]
      configuration = {
        ProjectName          = local.project["infra"]
        PrimarySource        = "Source"
        EnvironmentVariables = local.env_json["infra/apply-dev"]
      }
    }
  }

  stage {
    name = "PlanStaging"
    action {
      name             = "Plan"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["Source"]
      output_artifacts = ["PlanStaging"]
      configuration = {
        ProjectName          = local.project["infra"]
        EnvironmentVariables = local.env_json["infra/plan-staging"]
      }
    }
  }

  stage {
    name = "ApproveStaging"
    action {
      name          = "ManualApproval"
      category      = "Approval"
      owner         = "AWS"
      provider      = "Manual"
      version       = "1"
      configuration = local.approval_configuration
    }
  }

  stage {
    name = "ApplyStaging"
    action {
      name            = "Apply"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      run_order       = 1
      input_artifacts = ["Source", "PlanStaging"]
      configuration = {
        ProjectName          = local.project["infra"]
        PrimarySource        = "Source"
        EnvironmentVariables = local.env_json["infra/apply-staging"]
      }
    }
    action {
      name            = "RecordCommit"
      category        = "Build"
      owner           = "AWS"
      provider        = "CodeBuild"
      version         = "1"
      run_order       = 2
      input_artifacts = ["Source"]
      configuration = {
        ProjectName          = local.project["record"]
        EnvironmentVariables = local.env_json["infra/record"]
      }
    }
  }
}
