"""Anomaly data models."""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Literal, Optional, Union


@dataclass
class DistributionAnomaly:
    """Anomalia na distribuição de scores."""
    
    type: Literal["distribution"] = "distribution"
    max_abs_diff: float = 0.0
    threshold: float = 0.0
    percentiles_actual: List[float] = None
    percentiles_expected: List[float] = None
    severity: Literal["low", "medium", "high"] = "low"
    
    def __post_init__(self):
        if self.percentiles_actual is None:
            self.percentiles_actual = []
        if self.percentiles_expected is None:
            self.percentiles_expected = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário JSON-compatível."""
        return asdict(self)


@dataclass
class LatencyAnomaly:
    """Anomalia na latência."""
    
    type: Literal["latency"] = "latency"
    avg_latency_ms: float = 0.0
    sla_ms: float = 0.0
    p95_latency_ms: Optional[float] = None
    severity: Literal["low", "medium", "high"] = "low"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário JSON-compatível."""
        return asdict(self)


@dataclass
class VolumeAnomaly:
    """Anomalia no volume de transações."""
    
    type: Literal["volume"] = "volume"
    actual_count: int = 0
    min_expected: Optional[int] = None
    max_expected: Optional[int] = None
    deviation_type: Literal["low", "high"] = "low"
    severity: Literal["low", "medium", "high"] = "low"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário JSON-compatível."""
        return asdict(self)


# Type alias para qualquer tipo de anomalia
Anomaly = Union[DistributionAnomaly, LatencyAnomaly, VolumeAnomaly]
