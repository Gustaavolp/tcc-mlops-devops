data "aws_caller_identity" "current" {}

# Saídas das stacks platform de cada ambiente: cluster EKS, repositórios ECR e
# URL de health da API (fonte única; nada é fixado nesta stack).
data "terraform_remote_state" "platform" {
  for_each = var.environments

  backend = "s3"
  config = {
    bucket = var.state_bucket
    key    = "${each.key}/platform/terraform.tfstate"
    region = var.state_bucket_region
  }
}
