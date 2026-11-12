project_name    = "elo-fraud"
repository_name = "compra-online-repo"
branch          = "main"
k8s_namespace   = "fraud-detection"

environments = {
  dev     = { region = "us-east-1" }
  staging = { region = "sa-east-1" }
}
