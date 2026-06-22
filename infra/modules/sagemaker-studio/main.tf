# -----------------------------------------------------------------------------
# SageMaker Studio Domain Module
# -----------------------------------------------------------------------------
#
# Este modulo cria um SageMaker Studio Domain completo com:
# - Studio Domain (PublicInternetOnly ou VpcOnly)
# - Security Group dedicado (criado automaticamente no modo VpcOnly)
# - IAM Execution Role
# - CloudWatch Log Group
# - Auto-shutdown de apps ociosos (JupyterLab e CodeEditor)
# - User Profiles
#
# No modo VpcOnly, o egress para servicos AWS e feito via NAT Gateway
# e/ou VPC Endpoints ja existentes na VPC.
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# IAM Role para Studio Execution
# -----------------------------------------------------------------------------

resource "aws_iam_role" "execution" {
  name               = var.execution_role_name
  assume_role_policy = data.aws_iam_policy_document.assume_role.json

  # Ignorar tags (SSO não tem permissão iam:TagRole)
  lifecycle {
    ignore_changes = [tags, tags_all]
  }
}

# Trust Policy
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
# IAM Policies
# -----------------------------------------------------------------------------

# Policy 1: SageMaker Full Access (AWS Managed)
resource "aws_iam_role_policy_attachment" "sagemaker_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

# -----------------------------------------------------------------------------
# AWS Managed Policy Attachments (S3 e CloudWatch)
# -----------------------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "s3_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# -----------------------------------------------------------------------------
# Policy: CodeCommit Access (AWS Managed)
# -----------------------------------------------------------------------------
# Permite GitPull/GitPush no CodeCommit para versionamento de código no Studio

resource "aws_iam_role_policy_attachment" "codecommit_power_user" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSCodeCommitPowerUser"
}

# -----------------------------------------------------------------------------
# Policy: Bedrock Full Access (AWS Managed)
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
# Acesso SQS para notebooks no Studio

resource "aws_iam_role_policy_attachment" "sqs_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
}

# -----------------------------------------------------------------------------
# Policy: DynamoDB Full Access (AWS Managed)
# -----------------------------------------------------------------------------
# Acesso DynamoDB (feature store) para notebooks no Studio

resource "aws_iam_role_policy_attachment" "dynamodb_full_access" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# -----------------------------------------------------------------------------
# Policy: Canvas Data Science Assistant (AWS Managed)
# -----------------------------------------------------------------------------
# Habilita Canvas Data Science Assistant no SageMaker Studio

resource "aws_iam_role_policy_attachment" "canvas_data_science_assistant" {
  role       = aws_iam_role.execution.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerCanvasSMDataScienceAssistantAccess"
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
# CloudWatch Log Group
# -----------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "studio" {
  name              = var.log_group_name
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name      = var.log_group_name
    Component = "SageMaker-Studio"
  })
}

# -----------------------------------------------------------------------------
# Security Group para Studio Domain (somente VpcOnly)
# -----------------------------------------------------------------------------

resource "aws_security_group" "studio" {
  count = var.app_network_access_type == "VpcOnly" ? 1 : 0

  name_prefix = "${var.domain_name}-studio-"
  description = "Security Group para SageMaker Studio Domain (VpcOnly)"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name      = "${var.domain_name}-studio-sg"
    Component = "SageMaker-Studio-SecurityGroup"
  })

  lifecycle {
    create_before_destroy = true
  }
}

# Ingress: comunicacao entre apps do Studio (self-referencing)
resource "aws_vpc_security_group_ingress_rule" "studio_self" {
  count = var.app_network_access_type == "VpcOnly" ? 1 : 0

  security_group_id            = aws_security_group.studio[0].id
  referenced_security_group_id = aws_security_group.studio[0].id
  from_port                    = 0
  to_port                      = 65535
  ip_protocol                  = "tcp"
  description                  = "Allow all TCP between Studio apps"

  tags = merge(var.tags, {
    Name = "${var.domain_name}-sg-self"
  })
}

# Ingress: NFS para montagem do EFS (home directories)
resource "aws_vpc_security_group_ingress_rule" "studio_nfs" {
  count = var.app_network_access_type == "VpcOnly" ? 1 : 0

  security_group_id            = aws_security_group.studio[0].id
  referenced_security_group_id = aws_security_group.studio[0].id
  from_port                    = 2049
  to_port                      = 2049
  ip_protocol                  = "tcp"
  description                  = "Allow NFS for EFS home directories"

  tags = merge(var.tags, {
    Name = "${var.domain_name}-sg-nfs-in"
  })
}

# Egress: HTTPS para servicos AWS (via NAT Gateway e VPC Endpoints existentes)
resource "aws_vpc_security_group_egress_rule" "studio_https" {
  count = var.app_network_access_type == "VpcOnly" ? 1 : 0

  security_group_id = aws_security_group.studio[0].id
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  cidr_ipv4         = "0.0.0.0/0"
  description       = "Allow HTTPS egress to AWS services"

  tags = merge(var.tags, {
    Name = "${var.domain_name}-sg-https-out"
  })
}

# Egress: NFS para EFS
resource "aws_vpc_security_group_egress_rule" "studio_nfs" {
  count = var.app_network_access_type == "VpcOnly" ? 1 : 0

  security_group_id = aws_security_group.studio[0].id
  from_port         = 2049
  to_port           = 2049
  ip_protocol       = "tcp"
  cidr_ipv4         = var.vpc_cidr
  description       = "Allow NFS egress for EFS"

  tags = merge(var.tags, {
    Name = "${var.domain_name}-sg-nfs-out"
  })
}

# Egress: DNS para resolucao de nomes
resource "aws_vpc_security_group_egress_rule" "studio_dns" {
  count = var.app_network_access_type == "VpcOnly" ? 1 : 0

  security_group_id = aws_security_group.studio[0].id
  from_port         = 53
  to_port           = 53
  ip_protocol       = "udp"
  cidr_ipv4         = var.vpc_cidr
  description       = "Allow DNS egress for name resolution"

  tags = merge(var.tags, {
    Name = "${var.domain_name}-sg-dns-out"
  })
}

# -----------------------------------------------------------------------------
# SageMaker Studio Domain
# -----------------------------------------------------------------------------

resource "aws_sagemaker_domain" "main" {
  domain_name = var.domain_name
  auth_mode   = "IAM"

  # Network Mode - PublicInternetOnly ou VpcOnly
  # PublicInternetOnly: Apps tem acesso direto a internet sem restricoes de VPC
  # VpcOnly: Apps so podem acessar recursos via VPC (requer NAT Gateway ou VPC Endpoints)
  app_network_access_type = var.app_network_access_type

  # VPC Configuration
  # O SageMaker ainda cria recursos na VPC (EFS para home directories)
  vpc_id     = var.vpc_id
  subnet_ids = var.subnet_ids

  # Default Execution Role
  default_user_settings {
    execution_role = aws_iam_role.execution.arn

    # Security Groups (obrigatorio no modo VpcOnly)
    security_groups = var.app_network_access_type == "VpcOnly" ? [aws_security_group.studio[0].id] : null

    # JupyterServer Settings
    jupyter_server_app_settings {
      default_resource_spec {
        instance_type       = "system"
        sagemaker_image_arn = null
      }
    }

    # KernelGateway (Notebook) Settings
    kernel_gateway_app_settings {
      default_resource_spec {
        instance_type       = var.default_notebook_instance_type
        sagemaker_image_arn = null
      }
    }

    # -------------------------------------------------------------------------
    # JupyterLab App Settings (com Idle Shutdown)
    # -------------------------------------------------------------------------
    jupyter_lab_app_settings {
      app_lifecycle_management {
        idle_settings {
          lifecycle_management        = var.lifecycle_management_enabled
          idle_timeout_in_minutes     = var.idle_timeout_in_minutes
          min_idle_timeout_in_minutes = var.idle_timeout_in_minutes
          max_idle_timeout_in_minutes = var.idle_timeout_in_minutes
        }
      }
    }

    # -------------------------------------------------------------------------
    # Code Editor App Settings (com Idle Shutdown)
    # -------------------------------------------------------------------------
    code_editor_app_settings {
      app_lifecycle_management {
        idle_settings {
          lifecycle_management        = var.lifecycle_management_enabled
          idle_timeout_in_minutes     = var.idle_timeout_in_minutes
          min_idle_timeout_in_minutes = var.idle_timeout_in_minutes
          max_idle_timeout_in_minutes = var.idle_timeout_in_minutes
        }
      }
    }

    # Sharing Settings
    sharing_settings {
      notebook_output_option = var.notebook_output_option
    }
  }

  tags = merge(var.tags, {
    Name      = var.domain_name
    Component = "SageMaker-Studio-Domain"
  })

  depends_on = [
    aws_iam_role_policy_attachment.sagemaker_full_access,
    aws_iam_role_policy_attachment.s3_full_access,
    aws_iam_role_policy_attachment.cloudwatch_logs_full_access,
    aws_cloudwatch_log_group.studio
  ]
}

# -----------------------------------------------------------------------------
# SageMaker User Profiles
# -----------------------------------------------------------------------------

resource "aws_sagemaker_user_profile" "users" {
  for_each = { for profile in var.user_profiles : profile.name => profile }

  domain_id         = aws_sagemaker_domain.main.id
  user_profile_name = each.value.name

  user_settings {
    execution_role = coalesce(each.value.execution_role_arn, aws_iam_role.execution.arn)

    jupyter_server_app_settings {
      default_resource_spec {
        instance_type = "system"
      }
    }

    kernel_gateway_app_settings {
      default_resource_spec {
        instance_type = var.default_notebook_instance_type
      }
    }
  }

  tags = merge(var.tags, {
    Name      = each.value.name
    Component = "SageMaker-Studio-UserProfile"
  })
}
