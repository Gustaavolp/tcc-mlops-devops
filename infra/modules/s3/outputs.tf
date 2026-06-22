# -----------------------------------------------------------------------------
# S3 Bucket Outputs
# -----------------------------------------------------------------------------

# Raw Data Bucket
output "raw_bucket_id" {
  description = "ID do bucket de dados raw"
  value       = aws_s3_bucket.raw.id
}

output "raw_bucket_arn" {
  description = "ARN do bucket de dados raw"
  value       = aws_s3_bucket.raw.arn
}

# Processed Data Bucket
output "processed_bucket_id" {
  description = "ID do bucket de dados processed"
  value       = aws_s3_bucket.processed.id
}

output "processed_bucket_arn" {
  description = "ARN do bucket de dados processed"
  value       = aws_s3_bucket.processed.arn
}

# Models Bucket
output "models_bucket_id" {
  description = "ID do bucket de modelos"
  value       = aws_s3_bucket.models.id
}

output "models_bucket_arn" {
  description = "ARN do bucket de modelos"
  value       = aws_s3_bucket.models.arn
}

# Logs Bucket
output "logs_bucket_id" {
  description = "ID do bucket de logs"
  value       = aws_s3_bucket.logs.id
}

output "logs_bucket_arn" {
  description = "ARN do bucket de logs"
  value       = aws_s3_bucket.logs.arn
}

# Resources Bucket
output "resources_bucket_id" {
  description = "ID do bucket de recursos"
  value       = aws_s3_bucket.resources.id
}

output "resources_bucket_arn" {
  description = "ARN do bucket de recursos"
  value       = aws_s3_bucket.resources.arn
}

# Reports Promotion Bucket
output "reports_promotion_bucket_id" {
  description = "ID do bucket de reports promotion"
  value       = aws_s3_bucket.reports_promotion.id
}

output "reports_promotion_bucket_arn" {
  description = "ARN do bucket de reports promotion"
  value       = aws_s3_bucket.reports_promotion.arn
}

# Reports Statistics Bucket
output "reports_statistics_bucket_id" {
  description = "ID do bucket de reports statistics"
  value       = aws_s3_bucket.reports_statistics.id
}

output "reports_statistics_bucket_arn" {
  description = "ARN do bucket de reports statistics"
  value       = aws_s3_bucket.reports_statistics.arn
}

