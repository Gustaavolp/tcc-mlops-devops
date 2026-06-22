"""Insight data model."""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Literal


@dataclass
class Insight:
    """Insight analítico sobre métricas."""
    
    category: Literal["drift", "volume", "latency", "fraud_pattern"]
    message: str
    priority: int  # 1-5, onde 5 é mais importante
    related_metrics: Dict[str, Any]
    timestamp: str
    
    def __post_init__(self):
        """Valida campos após inicialização."""
        if not 1 <= self.priority <= 5:
            raise ValueError(f"Priority must be between 1 and 5, got {self.priority}")
        
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa para dicionário JSON-compatível."""
        return asdict(self)
