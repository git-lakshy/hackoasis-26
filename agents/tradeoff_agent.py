from typing import List
from data.types import OptimizationOpportunity
from data.cloud_manager import get_resource


def score_cost_impact(opp: OptimizationOpportunity) -> float:
    return min(opp.estimated_savings / 1000 * 10, 10.0)


def score_performance_impact(opp: OptimizationOpportunity) -> float:
    return {'resize': 8.0, 'schedule': 9.0, 'terminate': 5.0, 'delete': 7.0}.get(opp.action, 5.0)


def score_availability_impact(opp: OptimizationOpportunity, resource: dict) -> float:
    base = {'resize': 8, 'schedule': 9, 'terminate': 4, 'delete': 6}.get(opp.action, 5)
    if resource['env'] == 'prod':
        base -= 3
    elif resource['env'] == 'dev':
        base += 1
    return float(max(0, min(10, base)))


def run_tradeoff(opportunities: List[OptimizationOpportunity]) -> List[OptimizationOpportunity]:
    for opp in opportunities:
        resource = get_resource(opp.resource_id)
        opp.cost_score = score_cost_impact(opp)
        opp.perf_score = score_performance_impact(opp)
        opp.availability_score = score_availability_impact(opp, resource)
        opp.composite_score = round(opp.cost_score * 0.4 + opp.perf_score * 0.3 + opp.availability_score * 0.3, 4)
    return sorted(opportunities, key=lambda o: o.composite_score, reverse=True)
