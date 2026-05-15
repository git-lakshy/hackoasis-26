import json
from pathlib import Path
from typing import List
from data.types import OptimizationOpportunity, SimulationResult
from data.cloud_manager import get_resource
from memory.store import get_similar_outcomes

_CACHE = Path(__file__).parent.parent / 'data' / 'sim_cache.json'


def simulate_action(opp: OptimizationOpportunity) -> SimulationResult:
    resource = get_resource(opp.resource_id)
    monthly_cost = resource.get('monthly_cost', resource.get('daily_cost', 0) * 30)

    if opp.action == 'resize':
        result = SimulationResult(resource_id=opp.resource_id, action=opp.action,
            projected_savings=monthly_cost * 0.5,
            projected_utilization=min(resource.get('cpu_util', 0) * 1.8, 95),
            confidence=0.85, time_to_savings_days=7)
    elif opp.action == 'schedule':
        result = SimulationResult(resource_id=opp.resource_id, action=opp.action,
            projected_savings=monthly_cost * 0.4,
            projected_utilization=resource.get('cpu_util', 0),
            confidence=0.90, time_to_savings_days=3)
    else:
        result = SimulationResult(resource_id=opp.resource_id, action=opp.action,
            projected_savings=monthly_cost,
            projected_utilization=0.0,
            confidence=0.95, time_to_savings_days=1)

    history = get_similar_outcomes(resource.get('type', ''), opp.action)
    if history['count'] > 0:
        result.confidence = round(result.confidence * history['avg_accuracy'], 3)

    cache = []
    if _CACHE.exists():
        cache = json.loads(_CACHE.read_text())
    key = (opp.resource_id, opp.action)
    if not any(e['resource_id'] == opp.resource_id and e['action'] == opp.action for e in cache):
        cache.append(result.__dict__)
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE.write_text(json.dumps(cache, indent=2))

    return result


def run_simulation(opportunities: List[OptimizationOpportunity]) -> List[SimulationResult]:
    return [simulate_action(o) for o in opportunities]
