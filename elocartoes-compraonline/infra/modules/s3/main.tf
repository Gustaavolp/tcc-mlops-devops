# -----------------------------------------------------------------------------
# S3 Bucket 1: Raw Data
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "raw" {
  bucket = var.raw_bucket_name

  tags = merge(var.tags, {
    Name        = var.raw_bucket_name
    Environment = var.environment
    Purpose     = "Raw Data Storage"
  })
}

# -----------------------------------------------------------------------------
# S3 Bucket 2: Processed Data
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "processed" {
  bucket = var.processed_bucket_name

  tags = merge(var.tags, {
    Name        = var.processed_bucket_name
    Environment = var.environment
    Purpose     = "Processed Data Storage"
  })
}

# -----------------------------------------------------------------------------
# S3 Bucket 3: Models
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "models" {
  bucket = var.models_bucket_name

  tags = merge(var.tags, {
    Name        = var.models_bucket_name
    Environment = var.environment
    Purpose     = "ML Model Artifacts"
  })
}

# -----------------------------------------------------------------------------
# S3 Bucket 4: Logs
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "logs" {
  bucket = var.logs_bucket_name

  tags = merge(var.tags, {
    Name        = var.logs_bucket_name
    Environment = var.environment
    Purpose     = "Centralized Logs"
  })
}

# -----------------------------------------------------------------------------
# S3 Bucket 5: Resources
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "resources" {
  bucket = var.resources_bucket_name

  tags = merge(var.tags, {
    Name        = var.resources_bucket_name
    Environment = var.environment
    Purpose     = "Static Resources"
  })
}

# -----------------------------------------------------------------------------
# S3 Bucket 6: Reports Promotion
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "reports_promotion" {
  bucket = var.reports_promotion_bucket_name

  tags = merge(var.tags, {
    Name        = var.reports_promotion_bucket_name
    Environment = var.environment
    Purpose     = "Promotion Reports"
  })
}

# -----------------------------------------------------------------------------
# S3 Bucket 7: Reports Statistics
# -----------------------------------------------------------------------------

resource "aws_s3_bucket" "reports_statistics" {
  bucket = var.reports_statistics_bucket_name

  tags = merge(var.tags, {
    Name        = var.reports_statistics_bucket_name
    Environment = var.environment
    Purpose     = "Statistics Reports"
  })
}
