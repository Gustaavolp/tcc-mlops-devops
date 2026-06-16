# -----------------------------------------------------------------------------
# Glue Module - Main
# -----------------------------------------------------------------------------
#
# Este módulo cria uma infraestrutura completa para Glue ETL:
# - IAM Role com permissões necessárias
# - S3 Bucket para assets (scripts, logs, temp files)
# - Upload de script Python para S3
# - Glue Job (ETL)
# - Glue Trigger (SCHEDULED)
#
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# IAM Role for Glue Jobs
# -----------------------------------------------------------------------------

resource "aws_iam_role" "glue" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "glue.amazonaws.com"
      }
    }]
  })

}

# -----------------------------------------------------------------------------
# Managed Policy Attachments
# -----------------------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "glue_s3" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "glue_console" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:aws:iam::aws:policy/AWSGlueConsoleFullAccess"
}

resource "aws_iam_role_policy_attachment" "glue_logs" {
  role       = aws_iam_role.glue.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
}

# -----------------------------------------------------------------------------
# S3 Bucket - Glue Assets
# -----------------------------------------------------------------------------
# Bucket para armazenar scripts, logs e arquivos temporários do Glue

resource "aws_s3_bucket" "glue_assets" {
  bucket = var.assets_bucket_name

}

resource "aws_s3_bucket_versioning" "glue_assets" {
  bucket = aws_s3_bucket.glue_assets.id

  versioning_configuration {
    status = "Enabled"
  }
}

# -----------------------------------------------------------------------------
# S3 Upload - Scripts ETL
# -----------------------------------------------------------------------------
# Scripts Python são versionados no repositório e enviados ao S3 via Terraform

resource "aws_s3_object" "script" {
  bucket = aws_s3_bucket.glue_assets.id
  key    = var.script_s3_key
  source = var.script_local_path
  etag   = filemd5(var.script_local_path)

  depends_on = [aws_s3_bucket.glue_assets]

}

# -----------------------------------------------------------------------------
# Glue Job
# -----------------------------------------------------------------------------

resource "aws_glue_job" "main" {
  name        = var.job_name
  description = var.job_description
  role_arn    = aws_iam_role.glue.arn

  glue_version      = var.glue_version
  worker_type       = var.worker_type
  number_of_workers = var.number_of_workers
  timeout           = var.timeout
  max_retries       = var.max_retries

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.glue_assets.id}/${aws_s3_object.script.key}"
    python_version  = var.python_version
  }

  default_arguments = var.default_arguments

  execution_property {
    max_concurrent_runs = var.max_concurrent_runs
  }

  depends_on = [aws_s3_object.script]

}

# -----------------------------------------------------------------------------
# Glue Trigger - SCHEDULED
# -----------------------------------------------------------------------------

resource "aws_glue_trigger" "scheduled" {
  name     = var.trigger_name
  type     = "SCHEDULED"
  schedule = var.trigger_schedule

  actions {
    job_name = aws_glue_job.main.name
  }

  depends_on = [aws_glue_job.main]

}