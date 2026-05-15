from typing import List, Tuple
from data.types import OptimizationOpportunity, SimulationResult, RiskAssessment
from data.cloud_manager import get_resource
from memory.store import get_approval_pattern


def assess_risk(opp: OptimizationOpportunity, sim: SimulationResult) -> RiskAssessment:
    resource = get_resource(opp.resource_id)
    score, factors = 0, []

    if resource['env'] == 'prod':
        score += 30; factors.append('Production environment')
    if resource['type'] in ['rds', 'database', 'db']:
        score += 25; factors.append('Database resource')
    if opp.action == 'terminate':
        score += 20; factors.append('Destructive action: terminate')
    if opp.action == 'delete':
        score += 15; factors.append('Destructive action: delete')
    if sim.projected_savings > 500:
        score += 10; factors.append('High savings (>$500/mo)')
    if opp.availability_score < 5:
        score += 15; factors.append('Availability impact')

    tier = 'low' if score < 30 else ('medium' if score < 60 else 'high')
    pattern = get_approval_pattern(opp.action)
    if pattern['count'] > 0 and pattern['approve_rate'] < 0.3 and tier != 'high':
        tier = 'high' if tier == 'medium' else 'medium'
        factors.append(f'Historically low approval rate ({pattern["approve_rate"]:.0%})')

    return RiskAssessment(resource_id=opp.resource_id, action=opp.action,
                          risk_score=min(score, 100), risk_tier=tier, risk_factors=factors)


def gate_actions(opps, sims, risks) -> dict:
    auto_queue, approval_queue = [], []
    for opp, sim, risk in zip(opps, sims, risks):
        (approval_queue if risk.risk_tier == 'high' else auto_queue).append((opp, sim, risk))
    return {'auto_queue': auto_queue, 'approval_queue': approval_queue}
