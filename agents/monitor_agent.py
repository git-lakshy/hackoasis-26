import random
from typing import List
from data.types import WasteFinding
from data.mock_cloud import get_resources, get_resource

def scan_idle_resources(cpu_threshold=5.0):
    return [r for r in get_resources(None, None, None) if r.get("cpu_util", 0) < cpu_threshold]

def scan_underutilized(cpu_threshold=20.0):
    return [r for r in get_resources(None, None, None) if 5.0 <= r.get("cpu_util", 0) < cpu_threshold]

def scan_orphaned_resources():
    return [r for r in get_resources(None, None, None)
            if r.get("status") == "unattached" or (r.get("type") == "load_balancer" and r.get("targets", 1) == 0)]

def get_cost_trend(resource_id):
    r = get_resource(resource_id)
    base = r.get("monthly_cost", r.get("daily_cost", 0) * 30) / 30
    return [round(base + random.uniform(-0.5, 0.5), 2) for _ in range(7)]

def run_monitor_scan() -> List[WasteFinding]:
    seen = set()
    findings = []

    for r in scan_idle_resources():
        rid = r["id"]
        if rid in seen:
            continue
        seen.add(rid)
        mc = r.get("monthly_cost", r.get("daily_cost", 0) * 30)
        severity = "high" if mc > 100 else "medium"
        findings.append(WasteFinding(rid, "idle", mc, "", severity))

    for r in scan_orphaned_resources():
        rid = r["id"]
        if rid in seen:
            continue
        seen.add(rid)
        mc = r.get("monthly_cost", r.get("daily_cost", 0) * 30)
        findings.append(WasteFinding(rid, "orphaned", mc, "", "medium"))

    for r in scan_underutilized():
        rid = r["id"]
        if rid in seen:
            continue
        seen.add(rid)
        mc = r.get("monthly_cost", r.get("daily_cost", 0) * 30)
        findings.append(WasteFinding(rid, "oversized", mc, "", "low"))

    return findings
