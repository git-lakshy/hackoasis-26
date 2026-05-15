from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class WasteFinding:
    resource_id: str
    waste_type: str  # idle | oversized | orphaned | scheduled
    monthly_cost: float
    root_cause: str
    severity: str  # low | medium | high

@dataclass
class OptimizationOpportunity:
    resource_id: str
    action: str  # resize | schedule | terminate | delete
    estimated_savings: float
    cost_score: float = 0.0
    perf_score: float = 0.0
    availability_score: float = 0.0
    composite_score: float = 0.0

@dataclass
class SimulationResult:
    resource_id: str
    action: str
    projected_savings: float
    projected_utilization: float
    confidence: float
    time_to_savings_days: int

@dataclass
class RiskAssessment:
    resource_id: str
    action: str
    risk_score: int
    risk_tier: str  # low | medium | high
    risk_factors: List[str] = field(default_factory=list)

@dataclass
class ActionRecord:
    action_id: str
    resource_id: str
    action: str
    risk_tier: str
    simulated_savings: float
    actual_savings: Optional[float]
    accuracy: Optional[float]
    timestamp: str
    reasoning: str
    before_state: dict
    after_state: dict
