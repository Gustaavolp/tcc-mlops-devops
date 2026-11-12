# Stack aplicada manualmente (uma vez e a cada mudança nos pipelines): o pipeline
# de infraestrutura valida esta stack, mas não a aplica, para não alterar a si mesmo.
terraform {
  backend "s3" {
    bucket       = "elo-fraud-terraform-state-888577064416-us-east-1"
    key          = "shared/cicd/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
