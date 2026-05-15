"""
Prometheus integration.
Queries Prometheus for CPU/memory utilization to enrich resource findings.
Requires: requests
"""
import os
import requests
from datetime import datetime, timedelta, timezone

PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")


def _query(promql: str) -> list:
    """Run an instant PromQL query, return list of (labels, value) tuples."""
    try:
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query",
            params={"query": promql},
            timeout=5,
        )
        resp.raise_for_status()
        data = resp.json()
        return [
            (r["metric"], float(r["value"][1]))
            for r in data.get("data", {}).get("result", [])
        ]
    except Exception:
        return []


def _query_range(promql: str, hours: int = 24) -> float:
    """Run a range query and return the average value."""
    try:
        end = datetime.now(timezone.utc)
        start = end - timedelta(hours=hours)
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/query_range",
            params={
                "query": promql,
                "start": start.isoformat(),
                "end": end.isoformat(),
                "step": "1h",
            },
            timeout=5,
        )
        resp.raise_for_status()
        results = resp.json().get("data", {}).get("result", [])
        values = [float(v[1]) for r in results for v in r.get("values", [])]
        return round(sum(values) / len(values), 4) if values else 0.0
    except Exception:
        return 0.0


def get_idle_instances(cpu_threshold: float = 0.05) -> list:
    """
    Return instances with avg CPU < threshold over last 24h.
    Uses node_exporter / kube-state-metrics style metrics.
    """
    promql = (
        f'avg by (instance) '
        f'(rate(node_cpu_seconds_total{{mode!="idle"}}[24h])) < {cpu_threshold}'
    )
    return [
        {"instance": labels.get("instance", "unknown"), "cpu_avg": value}
        for labels, value in _query(promql)
    ]


def get_high_memory_instances(mem_threshold: float = 0.85) -> list:
    """Return instances with memory utilization > threshold."""
    promql = (
        f'(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) > {mem_threshold}'
    )
    return [
        {"instance": labels.get("instance", "unknown"), "mem_util": value}
        for labels, value in _query(promql)
    ]


def get_pod_cpu_avg(pod_name: str, namespace: str = "default", hours: int = 24) -> float:
    """Get average CPU usage for a specific pod."""
    promql = (
        f'avg(rate(container_cpu_usage_seconds_total{{'
        f'pod="{pod_name}",namespace="{namespace}",container!="POD"}}[5m]))'
    )
    return _query_range(promql, hours)


def enrich_resources_with_prometheus(resources: list) -> list:
    """
    Enrich a list of resource dicts with real CPU data from Prometheus.
    Falls back to existing cpu_util if Prometheus returns nothing.
    """
    if not is_available():
        return resources

    # Build a map of instance -> cpu from Prometheus
    promql = 'avg by (instance) (rate(node_cpu_seconds_total{mode!="idle"}[1h])) * 100'
    prom_cpu = {labels.get("instance", ""): value for labels, value in _query(promql)}

    for r in resources:
        # Try to match by resource id or instance name
        rid = r.get("id", "")
        for key, cpu in prom_cpu.items():
            if rid in key or key in rid:
                r["cpu_util"] = round(cpu, 2)
                r["_prom_enriched"] = True
                break
    return resources


def push_optimization_metric(action: str, savings: float, resource_id: str):
    """
    Push a custom metric to Prometheus Pushgateway when an optimization is executed.
    Requires PROMETHEUS_PUSHGATEWAY_URL env var.
    """
    pushgw = os.getenv("PROMETHEUS_PUSHGATEWAY_URL")
    if not pushgw:
        return
    try:
        payload = (
            f'# HELP finops_optimization_savings_dollars Monthly savings from optimization\n'
            f'# TYPE finops_optimization_savings_dollars gauge\n'
            f'finops_optimization_savings_dollars{{action="{action}",resource="{resource_id}"}} {savings}\n'
        )
        requests.post(
            f"{pushgw}/metrics/job/finops_optimizer/instance/{resource_id}",
            data=payload,
            timeout=5,
        )
    except Exception:
        pass


def is_available() -> bool:
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/-/healthy", timeout=3)
        return resp.status_code == 200
    except Exception:
        return False
