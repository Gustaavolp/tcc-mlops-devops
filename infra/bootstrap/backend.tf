# -----------------------------------------------------------------------------
# Backend do próprio bootstrap
# -----------------------------------------------------------------------------
# O bootstrap cria o bucket de estado; por isso o PRIMEIRO apply é feito com
# estado local e, em seguida, o estado é migrado para o próprio bucket:
#
#   1. comente o bloco abaixo e rode: terraform init && terraform apply
#   2. descomente o bloco e rode:     terraform init -migrate-state
#
# A partir daí o pipeline de infraestrutura (pipelines/scripts/tf_stacks.sh) planeja
# e aplica o bootstrap de forma idempotente, como as demais stacks.
# O nome do bucket deve coincidir com var.state_bucket_name (terraform.tfvars).
# -----------------------------------------------------------------------------

terraform {
  backend "s3" {
    bucket       = "elo-fraud-terraform-state-888577064416-us-east-1"
    key          = "bootstrap/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}
