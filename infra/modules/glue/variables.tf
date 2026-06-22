# -----------------------------------------------------------------------------
# Glue Module - Variables
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# IAM Role Configuration
# -----------------------------------------------------------------------------

variable "role_name" {
  description = "Nome da IAM Role para Glue Jobs"
  type        = string
}

# -----------------------------------------------------------------------------
# S3 Assets Bucket Configuration
# -----------------------------------------------------------------------------

variable "assets_bucket_name" {
  description = "Nome do S3 bucket para assets Glue"
  type        = string
}

# -----------------------------------------------------------------------------
# Script Configuration
# -----------------------------------------------------------------------------

variable "script_s3_key" {
  description = "Chave no S3 do script Python (ex: scripts/job_training_test_1.py)"
  type        = string
}

variable "script_local_path" {
  description = "Caminho local do script Python"
  type        = string
}

# -----------------------------------------------------------------------------
# Glue Job Configuration
# -----------------------------------------------------------------------------

variable "job_name" {
  description = "Nome do Glue Job na AWS"
  type        = string
}

variable "job_description" {
  description = "Descricao do Glue Job"
  type        = string
}

variable "glue_version" {
  description = "Versao do AWS Glue (ex: 5.0)"
  type        = string
}

variable "worker_type" {
  description = "Tipo de worker (G.1X, G.2X, etc)"
  type        = string
}

variable "number_of_workers" {
  description = "Numero de workers para processamento paralelo"
  type        = number
}

variable "timeout" {
  description = "Timeout do job em minutos"
  type        = number
}

variable "max_retries" {
  description = "Numero maximo de retentativas"
  type        = number
}

variable "max_concurrent_runs" {
  description = "Runs concorrentes maximas"
  type        = number
  default     = 1
}

variable "default_arguments" {
  description = "Argumentos padrao do Glue Job"
  type        = map(string)
}

# -----------------------------------------------------------------------------
# Trigger Configuration
# -----------------------------------------------------------------------------

variable "trigger_name" {
  description = "Nome do trigger SCHEDULED"
  type        = string
}

variable "trigger_schedule" {
  description = "Expressao cron do trigger (ex: cron(0 8 ? * SUN *))"
  type        = string
}

# -----------------------------------------------------------------------------
# Python Configuration
# -----------------------------------------------------------------------------

variable "python_version" {
  description = "Versao do Python para jobs Glue (2 ou 3)"
  type        = string
  default     = "3"

  validation {
    condition     = contains(["2", "3"], var.python_version)
    error_message = "python_version deve ser 2 ou 3"
  }
}
