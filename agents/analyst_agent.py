from typing import List
from data.types import WasteFinding
from data.mock_cloud import get_resources, get_resource

_ROOT_CAUSES = {
    "idle": "No active workload detected for 7+ days",
    "oversized": "Over-provisioned at launch, workload lighter than estimated",
    "orphaned": "Resource detached and forgotten after workload migration",
    "scheduled": "Dev resource running outside business hours",
}

def analyze_resource(resource_id):
    r = get_resource(resource_id).copy()
    peers = [x for x in get_resources() if x.get("type") == r.get("type") and x["id"] != resource_id]
    r["peer_avg_cpu"] = round(sum(p.get("cpu_util", 0) for p in peers) / len(peers), 2) if peers else 0.0
    return r

def calculate_waste_cost(resource_id, waste_type="idle"):
    r = get_resource(resource_id)
    monthly = r.get("monthly_cost", r.get("daily_cost", 0) * 30)
    return monthly * 0.6 if waste_type == "oversized" else monthly

def get_peer_comparison(resource_id):
    r = get_resource(resource_id)
    peers = [x for x in get_resources() if x.get("type") == r.get("type") and x["id"] != resource_id]
    return {
        "peer_avg_cpu": round(sum(p.get("cpu_util", 0) for p in peers) / len(peers), 2) if peers else 0.0,
        "peer_count": len(peers),
        "resource_cpu": r.get("cpu_util", 0),
    }

def identify_root_cause(resource_id, waste_type):
    return _ROOT_CAUSES.get(waste_type, "Unknown waste pattern")

def run_analyst(findings: List[WasteFinding]) -> List[WasteFinding]:
    return [
        WasteFinding(f.resource_id, f.waste_type,
                     calculate_waste_cost(f.resource_id, f.waste_type),
                     identify_root_cause(f.resource_id, f.waste_type),
                     f.severity)
        for f in findings
    ]
