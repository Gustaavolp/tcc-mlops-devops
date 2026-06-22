"""Configuration data model."""

import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class StatisticsConfig:
    """Configuração do sistema de statistics."""
    
    # Athena
    athena_database: str
    athena_workgroup: str
    athena_output_s3: str
    athena_table: str
    
    # Colunas e expressões
    score_expression: str
    timestamp_expression: Optional[str] = None
    latency_column: Optional[str] = None
    model_name_column: Optional[str] = None
    model_name_value: Optional[str] = None
    threshold_column: Optional[str] = None
    
    # Janela de tempo
    use_partitions: bool = True
    lookback_hours: int = 24
    partition_lookback_days: int = 1
    timezone_offset_hours: int = -3
    
    # Colunas de partição
    partition_year_column: str = "year"
    partition_month_column: str = "month"
    partition_day_column: str = "day"
    partition_hour_column: Optional[str] = None
    partition_lookback_hours: int = 24
    
    # Thresholds
    distribution_max_abs_diff: float = 0.05
    latency_sla_ms: float = 200.0
    volume_min: Optional[int] = None
    volume_max: Optional[int] = None
    
    # S3
    report_s3_uri: str = ""
    baseline_s3_uri: Optional[str] = None
    
    # Bedrock
    bedrock_model_id: str = "openai.gpt-oss-120b-1:0"
    bedrock_region: str = "us-east-1"
    
    # MLflow
    mlflow_app_arn: str = ""
    threshold_param_name: str = "optimal_threshold"
    exclude_debug_experiments: bool = True
    
    @classmethod
    def from_env(cls) -> "StatisticsConfig":
        """Cria configuração a partir de variáveis de ambiente."""
        
        # Score expression (obrigatório)
        score_expr = os.getenv("SCORE_EXPRESSION", "").strip()
        if not score_expr:
            score_expr = os.getenv("SCORE_COLUMN", "score").strip()
        
        # Timestamp expression (opcional se usar partições)
        timestamp_expr = os.getenv("SCORE_TIMESTAMP_EXPRESSION", "").strip()
        if not timestamp_expr:
            timestamp_expr = os.getenv("SCORE_TIMESTAMP_COLUMN", "").strip() or None
        
        # Baseline S3 URI
        baseline_uri = os.getenv("EXPECTED_PERCENTILES_S3_URI", "").strip()
        if not baseline_uri:
            baseline_uri = os.getenv("EXPECTED_DISTRIBUTION_S3_URI", "").strip() or None
        
        # Volume limits
        volume_min_str = os.getenv("VOLUME_MIN_EXPECTED", "").strip()
        volume_max_str = os.getenv("VOLUME_MAX_EXPECTED", "").strip()
        
        return cls(
            # Athena (obrigatórios)
            athena_database=os.getenv("ATHENA_DATABASE", "elo_fraud_dev_db"),
            athena_workgroup=os.getenv("ATHENA_WORKGROUP", "elo-fraud-athena-workgroup-dev"),
            athena_output_s3=os.getenv(
                "ATHENA_OUTPUT_S3",
                "s3://aws-athena-query-results-888577064416-us-east-1/",
            ),
            athena_table=os.getenv("ATHENA_TABLE", "inference_logs"),
            
            # Score e timestamp
            score_expression=score_expr,
            timestamp_expression=timestamp_expr,
            latency_column=os.getenv("LATENCY_COLUMN", "").strip() or None,
            model_name_column=os.getenv("MODEL_NAME_COLUMN", "").strip() or None,
            model_name_value=os.getenv("MODEL_NAME_VALUE", "").strip() or None,
            threshold_column=os.getenv("THRESHOLD_COLUMN", "threshold").strip() or None,
            
            # Janela de tempo
            use_partitions=os.getenv("STATISTICS_USE_PARTITIONS", "true").lower() != "false",
            lookback_hours=int(os.getenv("STATISTICS_LOOKBACK_HOURS", "24")),
            partition_lookback_days=int(os.getenv("STATISTICS_PARTITION_LOOKBACK_DAYS", "1")),
            timezone_offset_hours=int(os.getenv("STATISTICS_TIMEZONE_OFFSET_HOURS", "-3")),
            
            # Colunas de partição
            partition_year_column=os.getenv("PARTITION_YEAR_COLUMN", "year").strip(),
            partition_month_column=os.getenv("PARTITION_MONTH_COLUMN", "month").strip(),
            partition_day_column=os.getenv("PARTITION_DAY_COLUMN", "day").strip(),
            partition_hour_column=os.getenv("PARTITION_HOUR_COLUMN", "hour").strip() or None,
            partition_lookback_hours=int(os.getenv("STATISTICS_PARTITION_LOOKBACK_HOURS", "24")),
            
            # Thresholds
            distribution_max_abs_diff=float(os.getenv("DISTRIBUTION_MAX_ABS_DIFF", "0.05")),
            latency_sla_ms=float(os.getenv("LATENCY_SLA_MS", "200")),
            volume_min=int(volume_min_str) if volume_min_str else None,
            volume_max=int(volume_max_str) if volume_max_str else None,
            
            # S3
            report_s3_uri=os.getenv(
                "STATISTICS_REPORT_S3_URI",
                "s3://elo-fraud-reports-statistics-dev-888577064416"
            ),
            baseline_s3_uri=baseline_uri,
            
            # Bedrock
            bedrock_model_id=os.getenv("BEDROCK_MODEL_ID", "openai.gpt-oss-120b-1:0"),
            bedrock_region=os.getenv(
                "BEDROCK_REGION",
                os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
            ),
            
            # MLflow
            mlflow_app_arn=os.getenv(
                "MLFLOW_APP_ARN",
                "arn:aws:sagemaker:us-east-1:888577064416:mlflow-app/app-LNOFZM2USGXQ"
            ),
            threshold_param_name=os.getenv("THRESHOLD_PARAM_NAME", "optimal_threshold"),
            exclude_debug_experiments=os.getenv("EXCLUDE_DEBUG_EXPERIMENTS", "true").lower() != "false",
        )
    
    def validate(self) -> List[str]:
        """
        Valida configuração.
        
        Returns:
            Lista de variáveis obrigatórias faltantes ou erros de formato
        """
        errors = []
        
        # Variáveis obrigatórias
        if not self.athena_database:
            errors.append("ATHENA_DATABASE")
        if not self.athena_workgroup:
            errors.append("ATHENA_WORKGROUP")
        if not self.athena_output_s3:
            errors.append("ATHENA_OUTPUT_S3")
        if not self.athena_table:
            errors.append("ATHENA_TABLE")
        if not self.score_expression:
            errors.append("SCORE_COLUMN or SCORE_EXPRESSION")
        
        # Se não usar partições, timestamp é obrigatório
        if not self.use_partitions and not self.timestamp_expression:
            errors.append("SCORE_TIMESTAMP_EXPRESSION or SCORE_TIMESTAMP_COLUMN (required when not using partitions)")
        if self.partition_hour_column and self.partition_lookback_hours < 1:
            errors.append("STATISTICS_PARTITION_LOOKBACK_HOURS must be >= 1")
        
        # Validação de formato
        if self.report_s3_uri and not self.report_s3_uri.startswith("s3://"):
            errors.append("STATISTICS_REPORT_S3_URI must start with s3://")
        
        if self.baseline_s3_uri and not self.baseline_s3_uri.startswith("s3://"):
            errors.append("EXPECTED_PERCENTILES_S3_URI or EXPECTED_DISTRIBUTION_S3_URI must start with s3://")
        
        if self.athena_output_s3 and not self.athena_output_s3.startswith("s3://"):
            errors.append("ATHENA_OUTPUT_S3 must start with s3://")
        
        # Validação de valores numéricos
        if self.distribution_max_abs_diff < 0:
            errors.append("DISTRIBUTION_MAX_ABS_DIFF must be >= 0")
        
        if self.latency_sla_ms < 0:
            errors.append("LATENCY_SLA_MS must be >= 0")
        
        if self.volume_min is not None and self.volume_min < 0:
            errors.append("VOLUME_MIN_EXPECTED must be >= 0")
        
        if self.volume_max is not None and self.volume_max < 0:
            errors.append("VOLUME_MAX_EXPECTED must be >= 0")
        
        if self.volume_min is not None and self.volume_max is not None:
            if self.volume_min > self.volume_max:
                errors.append("VOLUME_MIN_EXPECTED must be <= VOLUME_MAX_EXPECTED")
        
        return errors
