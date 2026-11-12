# Monorepo: um único repositório; cada pipeline observa apenas os caminhos do seu
# artefato (pipelines/scripts/detect_changes.sh).
resource "aws_codecommit_repository" "main" {
  count = var.create_repository ? 1 : 0

  repository_name = var.repository_name
  description     = "Plataforma MLOps de detecção de fraude (monorepo)"
  default_branch  = var.branch

  lifecycle {
    # default_branch só pode ser definido após o primeiro push
    ignore_changes = [default_branch]
  }
}
