variable "aws_region" {
  type        = string
  description = "AWS region for Lambda and EventBridge."
  default     = "sa-east-1"
}

variable "lambda_name" {
  type        = string
  description = "Lambda function name."
  default     = "elo-fraud-promotion-reporter"
}

variable "lambda_runtime" {
  type        = string
  description = "Lambda runtime."
  default     = "python3.12"
}

variable "lambda_timeout" {
  type        = number
  description = "Lambda timeout in seconds."
  default     = 60
}

variable "lambda_memory" {
  type        = number
  description = "Lambda memory in MB."
  default     = 512
}

variable "log_retention_days" {
  type        = number
  description = "CloudWatch log retention in days."
  default     = 14
}

variable "schedule_expression" {
  type        = string
  description = "EventBridge schedule expression."
  default     = "cron(0 10 * * ? *)"
}

variable "mlflow_app_arn" {
  type        = string
  description = "MLflow App ARN."
  default     = "arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ"
}

variable "mlflow_app_region" {
  type        = string
  description = "Region where the MLflow App is hosted."
  default     = "us-east-1"
}

variable "promotion_report_s3_uri" {
  type        = string
  description = "S3 base URI for promotion reports."
  default     = "s3://elo-fraud-reports-promotion-dev-888577064416"
}

variable "promotion_report_bucket" {
  type        = string
  description = "S3 bucket name for promotion reports."
  default     = "elo-fraud-reports-promotion-dev-888577064416"
}

variable "bedrock_region" {
  type        = string
  description = "Bedrock runtime region."
  default     = "sa-east-1"
}

variable "bedrock_model_id" {
  type        = string
  description = "Bedrock model ID."
  default     = "openai.gpt-oss-120b-1:0"
}

variable "promotion_lookback_hours" {
  type        = number
  description = "Lookback window in hours."
  default     = 24
}

variable "exclude_debug_experiments" {
  type        = bool
  description = "Exclude experiments with debug in the name."
  default     = true
}

variable "allow_metric_fallback" {
  type        = bool
  description = "Allow fallback to secondary metric."
  default     = false
}

variable "fallback_metric" {
  type        = string
  description = "Fallback metric name."
  default     = "best_cv_score"
}

variable "statistics_lambda_name" {
  type        = string
  description = "Statistics Lambda function name."
  default     = "elo-fraud-score-statistics"
}

variable "statistics_lambda_timeout" {
  type        = number
  description = "Statistics Lambda timeout in seconds."
  default     = 120
}

variable "statistics_lambda_memory" {
  type        = number
  description = "Statistics Lambda memory in MB."
  default     = 512
}

variable "statistics_schedule_expression" {
  type        = string
  description = "Statistics EventBridge schedule expression."
  default     = "cron(30 10 * * ? *)"
}

variable "statistics_report_s3_uri" {
  type        = string
  description = "S3 base URI for statistics reports."
  default     = "s3://elo-fraud-reports-statistics-dev-888577064416"
}

variable "statistics_report_bucket" {
  type        = string
  description = "S3 bucket name for statistics reports."
  default     = "elo-fraud-reports-statistics-dev-888577064416"
}

variable "athena_region" {
  type        = string
  description = "Athena region."
  default     = "us-east-1"
}

variable "athena_database" {
  type        = string
  description = "Athena database."
  default     = "elo_fraud_dev_db"
}

variable "athena_workgroup" {
  type        = string
  description = "Athena workgroup."
  default     = "elo-fraud-athena-workgroup-dev"
}

variable "athena_output_s3" {
  type        = string
  description = "Athena output location (S3 URI)."
  default     = "s3://elo-fraud-athena-results-dev/"
}

variable "athena_table" {
  type        = string
  description = "Athena table with scored transactions."
  default     = "inference_logs"
}

variable "score_column" {
  type        = string
  description = "Score column name or expression."
  default     = "score"
}

variable "score_expression" {
  type        = string
  description = "Optional score expression override."
  default     = ""
}

variable "score_timestamp_expression" {
  type        = string
  description = "Timestamp expression for filtering."
  default     = ""
}

variable "score_timestamp_column" {
  type        = string
  description = "Timestamp column name."
  default     = ""
}

variable "latency_column" {
  type        = string
  description = "Latency column name."
  default     = ""
}

variable "model_name_column" {
  type        = string
  description = "Optional model name column for filtering."
  default     = ""
}

variable "model_name_value" {
  type        = string
  description = "Optional model name value for filtering."
  default     = ""
}

variable "statistics_lookback_hours" {
  type        = number
  description = "Lookback window in hours for statistics."
  default     = 24
}

variable "score_threshold" {
  type        = string
  description = "Optional score threshold override."
  default     = ""
}

variable "threshold_param_name" {
  type        = string
  description = "MLflow metric or param name for threshold."
  default     = "optimal_threshold"
}

variable "score_buckets" {
  type        = string
  description = "Comma-separated score bucket edges."
  default     = "0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0"
}

variable "expected_distribution_s3_uri" {
  type        = string
  description = "Optional S3 URI to expected distribution JSON."
  default     = ""
}

variable "expected_distribution_bucket" {
  type        = string
  description = "Optional bucket name for expected distribution."
  default     = ""
}

variable "distribution_max_abs_diff" {
  type        = number
  description = "Max abs diff threshold for distribution drift."
  default     = 0.05
}

variable "latency_sla_ms" {
  type        = number
  description = "Latency SLA in milliseconds."
  default     = 200
}

variable "statistics_use_partitions" {
  type        = bool
  description = "Use year/month/day partitions for statistics."
  default     = true
}

variable "statistics_partition_date" {
  type        = string
  description = "Optional partition date override (YYYY-MM-DD)."
  default     = ""
}

variable "statistics_partition_lookback_days" {
  type        = number
  description = "Lookback days for partition filtering."
  default     = 1
}

variable "statistics_timezone_offset_hours" {
  type        = number
  description = "Timezone offset hours for partition date."
  default     = -3
}

variable "partition_year_column" {
  type        = string
  description = "Partition year column."
  default     = "year"
}

variable "partition_month_column" {
  type        = string
  description = "Partition month column."
  default     = "month"
}

variable "partition_day_column" {
  type        = string
  description = "Partition day column."
  default     = "day"
}

variable "score_percentiles" {
  type        = string
  description = "Comma-separated percentiles for score distribution."
  default     = "0.1,0.25,0.5,0.75,0.9,0.95,0.99"
}
