output "repository_clone_url_http" {
  description = "URL HTTPS do repositório CodeCommit"
  value       = var.create_repository ? aws_codecommit_repository.main[0].clone_url_http : null
}

output "pipelines" {
  description = "Pipelines criados"
  value       = merge({ for a, p in aws_codepipeline.app : "app-${a}" => p.name }, { infra = aws_codepipeline.infra.name })
}

output "artifact_bucket" {
  description = "Bucket de artefatos do CodePipeline"
  value       = aws_s3_bucket.artifacts.bucket
}

output "codebuild_role_arns" {
  description = "Roles IAM dos projetos CodeBuild"
  value = {
    app     = aws_iam_role.codebuild_app.arn
    infra   = aws_iam_role.codebuild_infra.arn
    rollout = aws_iam_role.model_rollout.arn
  }
}
