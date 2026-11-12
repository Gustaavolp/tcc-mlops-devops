# -----------------------------------------------------------------------------
# ECR Repositories - Elastic Container Registry
# -----------------------------------------------------------------------------
#
# Este módulo cria repositórios Docker para armazenar imagens dos serviços:
# 1. inference - API de scoring em tempo real (EKS)
# 2. process - Worker assíncrono SQS consumer (EKS)
# 3. model - Container de modelo ML customizado (SageMaker)
# 4. best-model-register - Lambda para registro de modelos MLflow
# 5. etl-delta-filter - Lambda para processamento Delta Lake
# 6. training-launcher - Lambda para lancamento de jobs SageMaker
#
# Recursos:
# - Scan de vulnerabilidades automático
# - Lifecycle policies para gerenciar retenção
# - Criptografia at-rest (AES256 - padrão AWS)
# -----------------------------------------------------------------------------


# -----------------------------------------------------------------------------
# Repository: Inference Service
# -----------------------------------------------------------------------------

resource "aws_ecr_repository" "inference" {
  name                 = var.inference_repo_name
  image_tag_mutability = var.image_tag_mutability

  # Tags imutáveis, exceto as que casarem com os filtros (ex.: "latest", usada
  # apenas no bootstrap). As imagens do CI/CD usam a tag do commit.
  dynamic "image_tag_mutability_exclusion_filter" {
    for_each = var.image_tag_mutability_exclusion_filters
    content {
      filter      = image_tag_mutability_exclusion_filter.value
      filter_type = "WILDCARD"
    }
  }

  image_scanning_configuration {
    scan_on_push = var.enable_image_scanning
  }

  tags = merge(var.tags, {
    Name        = var.inference_repo_name
    Environment = var.environment
    Service     = "inference"
    Description = "Real-time fraud scoring service"
  })
}

# Lifecycle policy for inference repository
resource "aws_ecr_lifecycle_policy" "inference" {
  repository = aws_ecr_repository.inference.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expirar imagens sem tag após ${var.untagged_image_retention_days} dias"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_image_retention_days
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Manter apenas as últimas ${var.max_image_count} imagens"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_image_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Repository: Process Service
# -----------------------------------------------------------------------------

resource "aws_ecr_repository" "process" {
  name                 = var.process_repo_name
  image_tag_mutability = var.image_tag_mutability

  # Tags imutáveis, exceto as que casarem com os filtros (ex.: "latest", usada
  # apenas no bootstrap). As imagens do CI/CD usam a tag do commit.
  dynamic "image_tag_mutability_exclusion_filter" {
    for_each = var.image_tag_mutability_exclusion_filters
    content {
      filter      = image_tag_mutability_exclusion_filter.value
      filter_type = "WILDCARD"
    }
  }

  image_scanning_configuration {
    scan_on_push = var.enable_image_scanning
  }

  tags = merge(var.tags, {
    Name        = var.process_repo_name
    Environment = var.environment
    Service     = "process"
    Description = "Async worker for SQS consumer"
  })
}

# Lifecycle policy for process repository
resource "aws_ecr_lifecycle_policy" "process" {
  repository = aws_ecr_repository.process.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expirar imagens sem tag após ${var.untagged_image_retention_days} dias"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_image_retention_days
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Manter apenas as últimas ${var.max_image_count} imagens"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_image_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Repository: Model Service
# -----------------------------------------------------------------------------

resource "aws_ecr_repository" "model" {
  name                 = var.model_repo_name
  image_tag_mutability = var.image_tag_mutability

  # Tags imutáveis, exceto as que casarem com os filtros (ex.: "latest", usada
  # apenas no bootstrap). As imagens do CI/CD usam a tag do commit.
  dynamic "image_tag_mutability_exclusion_filter" {
    for_each = var.image_tag_mutability_exclusion_filters
    content {
      filter      = image_tag_mutability_exclusion_filter.value
      filter_type = "WILDCARD"
    }
  }

  image_scanning_configuration {
    scan_on_push = var.enable_image_scanning
  }

  tags = merge(var.tags, {
    Name        = var.model_repo_name
    Environment = var.environment
    Service     = "model"
    Description = "Custom ML model container for SageMaker"
  })
}

# Lifecycle policy for model repository
resource "aws_ecr_lifecycle_policy" "model" {
  repository = aws_ecr_repository.model.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expirar imagens sem tag após ${var.untagged_image_retention_days} dias"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_image_retention_days
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Manter apenas as últimas ${var.max_image_count} imagens"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_image_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Repository: Best Model Register (Lambda Container)
# -----------------------------------------------------------------------------
# Repositório para imagem Docker da Lambda que registra o melhor modelo
# do MLflow no SageMaker Model Registry.
# -----------------------------------------------------------------------------

resource "aws_ecr_repository" "best_model_register" {
  name                 = var.best_model_register_repo_name
  image_tag_mutability = var.image_tag_mutability

  # Tags imutáveis, exceto as que casarem com os filtros (ex.: "latest", usada
  # apenas no bootstrap). As imagens do CI/CD usam a tag do commit.
  dynamic "image_tag_mutability_exclusion_filter" {
    for_each = var.image_tag_mutability_exclusion_filters
    content {
      filter      = image_tag_mutability_exclusion_filter.value
      filter_type = "WILDCARD"
    }
  }

  image_scanning_configuration {
    scan_on_push = var.enable_image_scanning
  }

  tags = merge(var.tags, {
    Name        = var.best_model_register_repo_name
    Environment = var.environment
    Service     = "lambda"
    Description = "Lambda container for MLflow best model registration"
  })
}

# Lifecycle policy for best_model_register repository
resource "aws_ecr_lifecycle_policy" "best_model_register" {
  repository = aws_ecr_repository.best_model_register.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expirar imagens sem tag após ${var.untagged_image_retention_days} dias"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_image_retention_days
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Manter apenas as últimas ${var.max_image_count} imagens"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_image_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Repository: ETL Delta Filter (Lambda Container)
# -----------------------------------------------------------------------------
# Repositório para imagem Docker da Lambda que processa dados da landing zone
# e gera delta incremental usando Delta Lake.
# -----------------------------------------------------------------------------

resource "aws_ecr_repository" "etl_delta_filter" {
  name                 = var.etl_delta_filter_repo_name
  image_tag_mutability = var.image_tag_mutability

  # Tags imutáveis, exceto as que casarem com os filtros (ex.: "latest", usada
  # apenas no bootstrap). As imagens do CI/CD usam a tag do commit.
  dynamic "image_tag_mutability_exclusion_filter" {
    for_each = var.image_tag_mutability_exclusion_filters
    content {
      filter      = image_tag_mutability_exclusion_filter.value
      filter_type = "WILDCARD"
    }
  }

  image_scanning_configuration {
    scan_on_push = var.enable_image_scanning
  }

  tags = merge(var.tags, {
    Name        = var.etl_delta_filter_repo_name
    Environment = var.environment
    Service     = "lambda"
    Description = "Lambda container for ETL Delta Lake processing"
  })
}

# Lifecycle policy for etl_delta_filter repository
resource "aws_ecr_lifecycle_policy" "etl_delta_filter" {
  repository = aws_ecr_repository.etl_delta_filter.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expirar imagens sem tag após ${var.untagged_image_retention_days} dias"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_image_retention_days
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Manter apenas as últimas ${var.max_image_count} imagens"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_image_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Repository: Training Launcher (Lambda Container)
# -----------------------------------------------------------------------------
# Repositório para imagem Docker da Lambda que lanca jobs de treinamento
# SageMaker usando ModelTrainer SDK.
# -----------------------------------------------------------------------------

resource "aws_ecr_repository" "training_launcher" {
  name                 = var.training_launcher_repo_name
  image_tag_mutability = var.image_tag_mutability

  # Tags imutáveis, exceto as que casarem com os filtros (ex.: "latest", usada
  # apenas no bootstrap). As imagens do CI/CD usam a tag do commit.
  dynamic "image_tag_mutability_exclusion_filter" {
    for_each = var.image_tag_mutability_exclusion_filters
    content {
      filter      = image_tag_mutability_exclusion_filter.value
      filter_type = "WILDCARD"
    }
  }

  image_scanning_configuration {
    scan_on_push = var.enable_image_scanning
  }

  tags = merge(var.tags, {
    Name        = var.training_launcher_repo_name
    Environment = var.environment
    Service     = "lambda"
    Description = "Lambda container for SageMaker training job launcher"
  })
}

# Lifecycle policy for training_launcher repository
resource "aws_ecr_lifecycle_policy" "training_launcher" {
  repository = aws_ecr_repository.training_launcher.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Expirar imagens sem tag após ${var.untagged_image_retention_days} dias"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_image_retention_days
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Manter apenas as últimas ${var.max_image_count} imagens"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = var.max_image_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}
