import os
import random
from typing import List
from data.types import WasteFinding
from data.cloud_manager import get_resources, get_resource, get_resources_live

_CLOUD_MODE = os.getenv("CLOUD_MODE", "mock").lower()


def scan_idle_resources(resources, cpu_threshold=5.0):
    return [r for r in resources if r.get("cpu_util", 0) < cpu_threshold and r.get("status") == "running"]


def scan_underutilized(resources, cpu_threshold=20.0):
    return [r for r in resources if 5.0 <= r.get("cpu_util", 0) < cpu_threshold]


def scan_orphaned_resources(resources):
    return [r for r in resources
            if r.get("status") == "unattached"
            or (r.get("type") == "load_balancer" and r.get("targets", 1) == 0)]


def get_cost_trend(resource_id):
    r = get_resource(resource_id)
    if not r:
        return [0.0] * 7
    base = r.get("monthly_cost", r.get("daily_cost", 0) * 30) / 30
    return [round(base + random.uniform(-0.5, 0.5), 2) for _ in range(7)]


def _fetch_all_resources() -> list:
    """Fetch resources from all enabled cloud providers."""
    if _CLOUD_MODE == "mock":
        return get_resources(None, None, None)

    resources = []

    # AWS
    try:
        from data.aws_connector import fetch_aws_resources, is_available as aws_ok
        if aws_ok():
            resources += fetch_aws_resources()
            print("[monitor] AWS: fetched live resources")
    except Exception as e:
        print(f"[monitor] AWS fallback to mock: {e}")
        resources += [r for r in get_resources(None, None, None) if r["cloud"] == "aws"]

    # Azure
    try:
        from data.azure_connector import fetch_azure_resources, is_available as az_ok
        if az_ok():
            resources += fetch_azure_resources()
            print("[monitor] Azure: fetched live resources")
    except Exception as e:
        print(f"[monitor] Azure fallback to mock: {e}")
        resources += [r for r in get_resources(None, None, None) if r["cloud"] == "azure"]

    # GCP
    try:
        from data.gcp_connector import fetch_gcp_resources, is_available as gcp_ok
        if gcp_ok():
            resources += fetch_gcp_resources()
            print("[monitor] GCP: fetched live resources")
    except Exception as e:
        print(f"[monitor] GCP fallback to mock: {e}")
        resources += [r for r in get_resources(None, None, None) if r["cloud"] == "gcp"]

    # Kubernetes
    try:
        from data.k8s_connector import scan_k8s_waste, is_available as k8s_ok
        if k8s_ok():
            k8s_findings = scan_k8s_waste()
            # Convert K8s findings directly — returned separately in run_monitor_scan
            print(f"[monitor] K8s: {len(k8s_findings)} findings")
    except Exception as e:
        print(f"[monitor] K8s unavailable: {e}")

    # Enrich with Prometheus CPU data if available
    try:
        from data.prometheus_connector import enrich_resources_with_prometheus, is_available as prom_ok
        if prom_ok():
            resources = enrich_resources_with_prometheus(resources)
            print("[monitor] Prometheus: enriched CPU data")
    except Exception as e:
        print(f"[monitor] Prometheus unavailable: {e}")

    # Fall back to full mock if nothing was fetched
    if not resources:
        print("[monitor] No live resources fetched, using mock data")
        resources = get_resources(None, None, None)

    return resources


def run_monitor_scan() -> List[WasteFinding]:
    resources = _fetch_all_resources()
    seen = set()
    findings = []

    for r in scan_idle_resources(resources):
        rid = r["id"]
        if rid in seen:
            continue
        seen.add(rid)
        mc = r.get("monthly_cost", r.get("daily_cost", 0) * 30)
        findings.append(WasteFinding(rid, "idle", mc, "", "high" if mc > 100 else "medium"))

    for r in scan_orphaned_resources(resources):
        rid = r["id"]
        if rid in seen:
            continue
        seen.add(rid)
        mc = r.get("monthly_cost", r.get("daily_cost", 0) * 30)
        findings.append(WasteFinding(rid, "orphaned", mc, "", "medium"))

    for r in scan_underutilized(resources):
        rid = r["id"]
        if rid in seen:
            continue
        seen.add(rid)
        mc = r.get("monthly_cost", r.get("daily_cost", 0) * 30)
        findings.append(WasteFinding(rid, "oversized", mc, "", "low"))

    # K8s findings (always attempted regardless of CLOUD_MODE)
    try:
        from data.k8s_connector import scan_k8s_waste, is_available as k8s_ok
        if k8s_ok():
            for f in scan_k8s_waste():
                if f.resource_id not in seen:
                    seen.add(f.resource_id)
                    findings.append(f)
    except Exception:
        pass

    return findings
