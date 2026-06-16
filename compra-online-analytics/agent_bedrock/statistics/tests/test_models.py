"""Unit tests for data models."""

import json
import os
from datetime import datetime, timezone

import pytest

from models.anomalies import DistributionAnomaly, LatencyAnomaly, VolumeAnomaly
from models.insight import Insight
from models.config import StatisticsConfig


class TestDistributionAnomaly:
    """Tests for DistributionAnomaly model."""
    
    def test_creation_with_defaults(self):
        """Test creating anomaly with default values."""
        anomaly = DistributionAnomaly()
        assert anomaly.type == "distribution"
        assert anomaly.max_abs_diff == 0.0
        assert anomaly.threshold == 0.0
        assert anomaly.percentiles_actual == []
        assert anomaly.percentiles_expected == []
        assert anomaly.severity == "low"
    
    def test_creation_with_values(self):
        """Test creating anomaly with specific values."""
        anomaly = DistributionAnomaly(
            max_abs_diff=0.15,
            threshold=0.05,
            percentiles_actual=[0.1, 0.2, 0.3],
            percentiles_expected=[0.05, 0.15, 0.25],
            severity="high"
        )
        assert anomaly.max_abs_diff == 0.15
        assert anomaly.threshold == 0.05
        assert len(anomaly.percentiles_actual) == 3
        assert len(anomaly.percentiles_expected) == 3
        assert anomaly.severity == "high"
    
    def test_to_dict(self):
        """Test serialization to dict."""
        anomaly = DistributionAnomaly(
            max_abs_diff=0.1,
            threshold=0.05,
            percentiles_actual=[0.1, 0.2],
            percentiles_expected=[0.05, 0.15],
            severity="medium"
        )
        result = anomaly.to_dict()
        assert result["type"] == "distribution"
        assert result["max_abs_diff"] == 0.1
        assert result["threshold"] == 0.05
        assert result["severity"] == "medium"
    
    def test_json_serialization(self):
        """Test JSON serialization."""
        anomaly = DistributionAnomaly(
            max_abs_diff=0.1,
            threshold=0.05,
            percentiles_actual=[0.1, 0.2],
            percentiles_expected=[0.05, 0.15],
            severity="medium"
        )
        json_str = json.dumps(anomaly.to_dict())
        parsed = json.loads(json_str)
        assert parsed["type"] == "distribution"
        assert parsed["max_abs_diff"] == 0.1


class TestLatencyAnomaly:
    """Tests for LatencyAnomaly model."""
    
    def test_creation_with_defaults(self):
        """Test creating anomaly with default values."""
        anomaly = LatencyAnomaly()
        assert anomaly.type == "latency"
        assert anomaly.avg_latency_ms == 0.0
        assert anomaly.sla_ms == 0.0
        assert anomaly.p95_latency_ms is None
        assert anomaly.severity == "low"
    
    def test_creation_with_values(self):
        """Test creating anomaly with specific values."""
        anomaly = LatencyAnomaly(
            avg_latency_ms=250.5,
            sla_ms=200.0,
            p95_latency_ms=350.0,
            severity="high"
        )
        assert anomaly.avg_latency_ms == 250.5
        assert anomaly.sla_ms == 200.0
        assert anomaly.p95_latency_ms == 350.0
        assert anomaly.severity == "high"
    
    def test_to_dict_with_none(self):
        """Test serialization with None values."""
        anomaly = LatencyAnomaly(
            avg_latency_ms=250.0,
            sla_ms=200.0,
            p95_latency_ms=None,
            severity="medium"
        )
        result = anomaly.to_dict()
        assert result["p95_latency_ms"] is None


class TestVolumeAnomaly:
    """Tests for VolumeAnomaly model."""
    
    def test_creation_with_defaults(self):
        """Test creating anomaly with default values."""
        anomaly = VolumeAnomaly()
        assert anomaly.type == "volume"
        assert anomaly.actual_count == 0
        assert anomaly.min_expected is None
        assert anomaly.max_expected is None
        assert anomaly.deviation_type == "low"
        assert anomaly.severity == "low"
    
    def test_creation_low_volume(self):
        """Test creating low volume anomaly."""
        anomaly = VolumeAnomaly(
            actual_count=500,
            min_expected=1000,
            max_expected=5000,
            deviation_type="low",
            severity="high"
        )
        assert anomaly.actual_count == 500
        assert anomaly.min_expected == 1000
        assert anomaly.deviation_type == "low"
    
    def test_creation_high_volume(self):
        """Test creating high volume anomaly."""
        anomaly = VolumeAnomaly(
            actual_count=10000,
            min_expected=1000,
            max_expected=5000,
            deviation_type="high",
            severity="medium"
        )
        assert anomaly.actual_count == 10000
        assert anomaly.max_expected == 5000
        assert anomaly.deviation_type == "high"


class TestInsight:
    """Tests for Insight model."""
    
    def test_creation_with_timestamp(self):
        """Test creating insight with explicit timestamp."""
        timestamp = "2024-01-15T10:30:00Z"
        insight = Insight(
            category="drift",
            message="Distribution drift detected",
            priority=5,
            related_metrics={"psi": 0.3},
            timestamp=timestamp
        )
        assert insight.category == "drift"
        assert insight.message == "Distribution drift detected"
        assert insight.priority == 5
        assert insight.timestamp == timestamp
    
    def test_creation_auto_timestamp(self):
        """Test creating insight with auto-generated timestamp."""
        insight = Insight(
            category="volume",
            message="Low volume detected",
            priority=3,
            related_metrics={"count": 100},
            timestamp=""
        )
        # Should auto-generate timestamp
        assert insight.timestamp != ""
        # Should be valid ISO format
        datetime.fromisoformat(insight.timestamp.replace("Z", "+00:00"))
    
    def test_priority_validation(self):
        """Test priority validation."""
        with pytest.raises(ValueError, match="Priority must be between 1 and 5"):
            Insight(
                category="drift",
                message="Test",
                priority=0,
                related_metrics={},
                timestamp=""
            )
        
        with pytest.raises(ValueError, match="Priority must be between 1 and 5"):
            Insight(
                category="drift",
                message="Test",
                priority=6,
                related_metrics={},
                timestamp=""
            )
    
    def test_to_dict(self):
        """Test serialization to dict."""
        insight = Insight(
            category="latency",
            message="High latency detected",
            priority=4,
            related_metrics={"avg_ms": 300},
            timestamp="2024-01-15T10:30:00Z"
        )
        result = insight.to_dict()
        assert result["category"] == "latency"
        assert result["message"] == "High latency detected"
        assert result["priority"] == 4
        assert result["related_metrics"]["avg_ms"] == 300


class TestStatisticsConfig:
    """Tests for StatisticsConfig model."""
    
    def test_from_env_minimal(self, monkeypatch):
        """Test creating config from minimal environment variables."""
        monkeypatch.setenv("ATHENA_DATABASE", "test_db")
        monkeypatch.setenv("ATHENA_WORKGROUP", "test_wg")
        monkeypatch.setenv("ATHENA_OUTPUT_S3", "s3://test-bucket/output")
        monkeypatch.setenv("ATHENA_TABLE", "test_table")
        monkeypatch.setenv("SCORE_COLUMN", "fraud_score")
        
        config = StatisticsConfig.from_env()
        
        assert config.athena_database == "test_db"
        assert config.athena_workgroup == "test_wg"
        assert config.athena_output_s3 == "s3://test-bucket/output"
        assert config.athena_table == "test_table"
        assert config.score_expression == "fraud_score"
        
        # Check defaults
        assert config.use_partitions is True
        assert config.lookback_hours == 24
        assert config.distribution_max_abs_diff == 0.05
        assert config.latency_sla_ms == 200.0
    
    def test_from_env_with_optionals(self, monkeypatch):
        """Test creating config with optional variables."""
        monkeypatch.setenv("ATHENA_DATABASE", "test_db")
        monkeypatch.setenv("ATHENA_WORKGROUP", "test_wg")
        monkeypatch.setenv("ATHENA_OUTPUT_S3", "s3://test-bucket/output")
        monkeypatch.setenv("ATHENA_TABLE", "test_table")
        monkeypatch.setenv("SCORE_EXPRESSION", "cast(score as double)")
        monkeypatch.setenv("LATENCY_COLUMN", "latency_ms")
        monkeypatch.setenv("VOLUME_MIN_EXPECTED", "1000")
        monkeypatch.setenv("VOLUME_MAX_EXPECTED", "10000")
        monkeypatch.setenv("EXPECTED_PERCENTILES_S3_URI", "s3://test-bucket/baseline.json")
        monkeypatch.setenv("THRESHOLD_COLUMN", "threshold")
        monkeypatch.setenv("PARTITION_HOUR_COLUMN", "hour")
        monkeypatch.setenv("STATISTICS_PARTITION_LOOKBACK_HOURS", "12")
        
        config = StatisticsConfig.from_env()
        
        assert config.score_expression == "cast(score as double)"
        assert config.latency_column == "latency_ms"
        assert config.volume_min == 1000
        assert config.volume_max == 10000
        assert config.baseline_s3_uri == "s3://test-bucket/baseline.json"
        assert config.threshold_column == "threshold"
        assert config.partition_hour_column == "hour"
        assert config.partition_lookback_hours == 12
    
    def test_validate_success(self):
        """Test validation with valid config."""
        config = StatisticsConfig(
            athena_database="test_db",
            athena_workgroup="test_wg",
            athena_output_s3="s3://test-bucket/output",
            athena_table="test_table",
            score_expression="fraud_score",
            use_partitions=True,
            report_s3_uri="s3://test-bucket/reports"
        )
        
        errors = config.validate()
        assert errors == []
    
    def test_validate_missing_required(self):
        """Test validation with missing required fields."""
        config = StatisticsConfig(
            athena_database="",
            athena_workgroup="",
            athena_output_s3="",
            athena_table="",
            score_expression=""
        )
        
        errors = config.validate()
        assert "ATHENA_DATABASE" in errors
        assert "ATHENA_WORKGROUP" in errors
        assert "ATHENA_OUTPUT_S3" in errors
        assert "ATHENA_TABLE" in errors
        assert "SCORE_COLUMN or SCORE_EXPRESSION" in errors
    
    def test_validate_timestamp_required_without_partitions(self):
        """Test validation requires timestamp when not using partitions."""
        config = StatisticsConfig(
            athena_database="test_db",
            athena_workgroup="test_wg",
            athena_output_s3="s3://test-bucket/output",
            athena_table="test_table",
            score_expression="fraud_score",
            use_partitions=False,
            timestamp_expression=None
        )
        
        errors = config.validate()
        assert any("SCORE_TIMESTAMP" in err for err in errors)
    
    def test_validate_invalid_s3_uri(self):
        """Test validation catches invalid S3 URIs."""
        config = StatisticsConfig(
            athena_database="test_db",
            athena_workgroup="test_wg",
            athena_output_s3="invalid-uri",
            athena_table="test_table",
            score_expression="fraud_score",
            report_s3_uri="invalid-uri",
            baseline_s3_uri="invalid-uri"
        )
        
        errors = config.validate()
        assert any("ATHENA_OUTPUT_S3" in err and "s3://" in err for err in errors)
        assert any("STATISTICS_REPORT_S3_URI" in err and "s3://" in err for err in errors)
        assert any("EXPECTED_PERCENTILES_S3_URI" in err and "s3://" in err for err in errors)
    
    def test_validate_negative_thresholds(self):
        """Test validation catches negative thresholds."""
        config = StatisticsConfig(
            athena_database="test_db",
            athena_workgroup="test_wg",
            athena_output_s3="s3://test-bucket/output",
            athena_table="test_table",
            score_expression="fraud_score",
            distribution_max_abs_diff=-0.1,
            latency_sla_ms=-100.0,
            volume_min=-10,
            volume_max=-5
        )
        
        errors = config.validate()
        assert any("DISTRIBUTION_MAX_ABS_DIFF" in err and ">= 0" in err for err in errors)
        assert any("LATENCY_SLA_MS" in err and ">= 0" in err for err in errors)
        assert any("VOLUME_MIN_EXPECTED" in err and ">= 0" in err for err in errors)
        assert any("VOLUME_MAX_EXPECTED" in err and ">= 0" in err for err in errors)
    
    def test_validate_volume_min_greater_than_max(self):
        """Test validation catches min > max."""
        config = StatisticsConfig(
            athena_database="test_db",
            athena_workgroup="test_wg",
            athena_output_s3="s3://test-bucket/output",
            athena_table="test_table",
            score_expression="fraud_score",
            volume_min=10000,
            volume_max=1000
        )
        
        errors = config.validate()
        assert any("VOLUME_MIN_EXPECTED" in err and "<=" in err for err in errors)
