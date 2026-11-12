locals {
  account_id = data.aws_caller_identity.current.account_id
  dev_region = var.environments["dev"].region

  tags = merge({
    Project   = var.project_name
    ManagedBy = "Terraform"
    Stack     = "CICD"
  }, var.tags)

  repository_name = var.create_repository ? aws_codecommit_repository.main[0].repository_name : var.repository_name
  repository_arn  = "arn:aws:codecommit:${local.dev_region}:${local.account_id}:${var.repository_name}"

  # Artefatos conteinerizados (fonte única compartilhada com os scripts)
  artifacts = jsondecode(file("${path.module}/../../pipelines/artifacts.json")).artifacts

  # Saídas das stacks platform por ambiente
  platform = { for env, _ in var.environments : env => data.terraform_remote_state.platform[env].outputs }

  state_param_prefix = "/${var.project_name}/cicd"
  image_tag          = "#{SourceVariables.CommitId}" # tag imutável = commit

  # Variáveis de implantação por artefato e ambiente (vazias são descartadas)
  deploy_vars = {
    for name, cfg in local.artifacts : name => {
      for env, env_cfg in var.environments : env => {
        for k, v in {
          ARTIFACT             = name
          TARGET_ENV           = env
          DEPLOY_KIND          = cfg.deploy_kind
          TARGET_REPO_URL      = local.platform[env][cfg.ecr_output]
          IMAGE_TAG            = local.image_tag
          HEALTH_URL           = local.platform[env].api_health_endpoint_url
          STATE_PARAM_PREFIX   = local.state_param_prefix
          EKS_CLUSTER          = cfg.deploy_kind == "eks" ? local.platform[env].eks_cluster_name : ""
          K8S_NAMESPACE        = cfg.deploy_kind == "eks" ? var.k8s_namespace : ""
          K8S_DEPLOYMENT       = try(cfg.k8s_deployment, "")
          MANIFEST_DIRS        = join(" ", [for d in try(cfg.manifest_dirs, []) : replace(d, "{env}", env)])
          LAMBDA_FUNCTION      = cfg.deploy_kind == "lambda" ? "${var.project_name}-${cfg.lambda_name}-${env}" : ""
          TRAINING_IMAGE_PARAM = cfg.deploy_kind == "training-image" ? "/${var.project_name}/${env}/training-image" : ""
        } : k => v if v != ""
      }
    }
  }

  # ARNs usados nas políticas IAM
  ecr_repository_arns = distinct(flatten([
    for name, cfg in local.artifacts : [
      for env, env_cfg in var.environments :
      "arn:aws:ecr:${env_cfg.region}:${local.account_id}:repository/${split("/", local.platform[env][cfg.ecr_output])[1]}"
    ]
  ]))
  lambda_function_arns = flatten([
    for name, cfg in local.artifacts : [
      for env, env_cfg in var.environments :
      "arn:aws:lambda:${env_cfg.region}:${local.account_id}:function:${var.project_name}-${cfg.lambda_name}-${env}"
    ] if cfg.deploy_kind == "lambda"
  ])
  eks_cluster_arns = [
    for env, env_cfg in var.environments :
    "arn:aws:eks:${env_cfg.region}:${local.account_id}:cluster/${local.platform[env].eks_cluster_name}"
  ]
  training_image_param_arns = [
    for env, env_cfg in var.environments :
    "arn:aws:ssm:${env_cfg.region}:${local.account_id}:parameter/${var.project_name}/${env}/training-image"
  ]
}
