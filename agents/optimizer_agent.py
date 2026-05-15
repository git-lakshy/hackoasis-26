from typing import List
from data.types import WasteFinding, OptimizationOpportunity
from data.mock_cloud import get_resource

def generate_options(finding_dict):
    wtype = finding_dict.get("waste_type", "idle")
    mc = finding_dict.get("monthly_cost", 0)
    if wtype == "idle":
        return [("terminate", mc), ("schedule", mc * 0.4)]
    if wtype == "oversized":
        return [("resize", mc * 0.5)]
    if wtype == "orphaned":
        return [("delete", mc)]
    if wtype == "scheduled":
        return [("schedule", mc * 0.4)]
    return []

def estimate_savings(resource_id, action):
    r = get_resource(resource_id)
    monthly = r.get("monthly_cost", r.get("daily_cost", 0) * 30)
    if action == "resize":
        return monthly * 0.5
    if action == "schedule":
        return monthly * 0.4
    return monthly

def rank_opportunities(opportunities):
    return sorted(opportunities, key=lambda o: o.estimated_savings, reverse=True)

def run_optimizer(findings: List[WasteFinding]) -> List[OptimizationOpportunity]:
    opportunities = []
    for f in findings:
        options = generate_options({"waste_type": f.waste_type, "monthly_cost": f.monthly_cost})
        if not options:
            continue
        action, savings = max(options, key=lambda x: x[1])
        if savings <= 0:
            continue
        cost_score = min(savings / 100, 1.0)
        perf_score = 0.8 if action in ("resize", "schedule") else 0.5
        avail_score = 0.9 if action == "schedule" else 0.6
        composite = round((cost_score + perf_score + avail_score) / 3, 4)
        opportunities.append(OptimizationOpportunity(
            f.resource_id, action, round(savings, 2),
            round(cost_score, 4), perf_score, avail_score, composite
        ))
    return rank_opportunities(opportunities)
