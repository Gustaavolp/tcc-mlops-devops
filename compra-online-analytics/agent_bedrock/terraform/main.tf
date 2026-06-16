provider "aws" {
  region = var.aws_region
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../promotion"
  output_path = "${path.module}/lambda.zip"
}

data "archive_file" "statistics_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../statistics"
  output_path = "${path.module}/statistics.zip"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.lambda_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "statistics_lambda" {
  name              = "/aws/lambda/${var.statistics_lambda_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_iam_role" "lambda_role" {
  name = "${var.lambda_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.lambda_name}-policy"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::${var.promotion_report_bucket}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:CreatePresignedMlflowAppUrl"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role" "statistics_lambda_role" {
  name = "${var.statistics_lambda_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

locals {
  statistics_getobject_resources = compact([
    "arn:aws:s3:::${var.statistics_report_bucket}/*",
    var.expected_distribution_bucket != "" ? "arn:aws:s3:::${var.expected_distribution_bucket}/*" : ""
  ])
}

resource "aws_iam_role_policy" "statistics_lambda_policy" {
  name = "${var.statistics_lambda_name}-policy"
  role = aws_iam_role.statistics_lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = "arn:aws:s3:::${var.statistics_report_bucket}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = local.statistics_getobject_resources
      },
      {
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:GetWorkGroup"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:CreatePresignedMlflowAppUrl"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_lambda_function" "promotion_reporter" {
  function_name    = var.lambda_name
  role             = aws_iam_role.lambda_role.arn
  handler          = "lambda_handler.lambda_handler"
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = {
      MLFLOW_APP_ARN              = var.mlflow_app_arn
      MLFLOW_APP_REGION           = var.mlflow_app_region
      PROMOTION_REPORT_S3_URI     = var.promotion_report_s3_uri
      BEDROCK_REGION              = var.bedrock_region
      BEDROCK_MODEL_ID            = var.bedrock_model_id
      PROMOTION_LOOKBACK_HOURS    = tostring(var.promotion_lookback_hours)
      EXCLUDE_DEBUG_EXPERIMENTS   = var.exclude_debug_experiments ? "true" : "false"
      ALLOW_METRIC_FALLBACK       = var.allow_metric_fallback ? "true" : "false"
      FALLBACK_METRIC             = var.fallback_metric
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

resource "aws_lambda_function" "statistics_reporter" {
  function_name    = var.statistics_lambda_name
  role             = aws_iam_role.statistics_lambda_role.arn
  handler          = "lambda_handler.lambda_handler"
  runtime          = var.lambda_runtime
  timeout          = var.statistics_lambda_timeout
  memory_size      = var.statistics_lambda_memory
  filename         = data.archive_file.statistics_zip.output_path
  source_code_hash = data.archive_file.statistics_zip.output_base64sha256

  environment {
    variables = {
      STATISTICS_REPORT_S3_URI     = var.statistics_report_s3_uri
      STATISTICS_LOOKBACK_HOURS    = tostring(var.statistics_lookback_hours)
      STATISTICS_USE_PARTITIONS    = var.statistics_use_partitions ? "true" : "false"
      STATISTICS_PARTITION_DATE    = var.statistics_partition_date
      STATISTICS_PARTITION_LOOKBACK_DAYS = tostring(var.statistics_partition_lookback_days)
      STATISTICS_TIMEZONE_OFFSET_HOURS  = tostring(var.statistics_timezone_offset_hours)
      PARTITION_YEAR_COLUMN        = var.partition_year_column
      PARTITION_MONTH_COLUMN       = var.partition_month_column
      PARTITION_DAY_COLUMN         = var.partition_day_column
      SCORE_COLUMN                 = var.score_column
      SCORE_EXPRESSION             = var.score_expression
      SCORE_TIMESTAMP_EXPRESSION   = var.score_timestamp_expression
      SCORE_TIMESTAMP_COLUMN       = var.score_timestamp_column
      LATENCY_COLUMN               = var.latency_column
      MODEL_NAME_COLUMN            = var.model_name_column
      MODEL_NAME_VALUE             = var.model_name_value
      SCORE_THRESHOLD              = var.score_threshold
      THRESHOLD_PARAM_NAME         = var.threshold_param_name
      SCORE_PERCENTILES            = var.score_percentiles
      EXPECTED_PERCENTILES_S3_URI  = var.expected_distribution_s3_uri
      EXPECTED_DISTRIBUTION_S3_URI = var.expected_distribution_s3_uri
      DISTRIBUTION_MAX_ABS_DIFF    = tostring(var.distribution_max_abs_diff)
      LATENCY_SLA_MS               = tostring(var.latency_sla_ms)
      ATHENA_REGION                = var.athena_region
      ATHENA_DATABASE              = var.athena_database
      ATHENA_WORKGROUP             = var.athena_workgroup
      ATHENA_OUTPUT_S3             = var.athena_output_s3
      ATHENA_TABLE                 = var.athena_table
      MLFLOW_APP_ARN               = var.mlflow_app_arn
      MLFLOW_APP_REGION            = var.mlflow_app_region
      EXCLUDE_DEBUG_EXPERIMENTS    = var.exclude_debug_experiments ? "true" : "false"
    }
  }

  depends_on = [aws_cloudwatch_log_group.statistics_lambda]
}

resource "aws_cloudwatch_event_rule" "daily" {
  name                = "${var.lambda_name}-daily"
  schedule_expression = var.schedule_expression
}

resource "aws_cloudwatch_event_rule" "statistics_daily" {
  name                = "${var.statistics_lambda_name}-daily"
  schedule_expression = var.statistics_schedule_expression
}

resource "aws_cloudwatch_event_target" "daily_target" {
  rule      = aws_cloudwatch_event_rule.daily.name
  target_id = "promotion_reporter"
  arn       = aws_lambda_function.promotion_reporter.arn
}

resource "aws_cloudwatch_event_target" "statistics_daily_target" {
  rule      = aws_cloudwatch_event_rule.statistics_daily.name
  target_id = "statistics_reporter"
  arn       = aws_lambda_function.statistics_reporter.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.promotion_reporter.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily.arn
}

resource "aws_lambda_permission" "allow_eventbridge_statistics" {
  statement_id  = "AllowExecutionFromEventBridgeStatistics"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.statistics_reporter.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.statistics_daily.arn
}
