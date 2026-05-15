"""
Kubernetes API connector.
Fetches pods, deployments, and nodes with resource requests/limits.
Requires: kubernetes (pip install kubernetes)
"""
import os
from datetime import datetime, timezone

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException
    _K8S_AVAILABLE = True
except ImportError:
    _K8S_AVAILABLE = False


def _load_config():
    kubeconfig = os.getenv("KUBECONFIG")
    in_cluster = os.getenv("K8S_IN_CLUSTER", "false").lower() == "true"
    if in_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config(config_file=kubeconfig or None)


def _parse_cpu(cpu_str: str) -> float:
    """Convert k8s CPU string (e.g. '250m', '1') to millicores float."""
    if not cpu_str:
        return 0.0
    if cpu_str.endswith("m"):
        return float(cpu_str[:-1])
    return float(cpu_str) * 1000


def _parse_mem_mb(mem_str: str) -> float:
    """Convert k8s memory string to MB."""
    if not mem_str:
        return 0.0
    units = {"Ki": 1/1024, "Mi": 1, "Gi": 1024, "Ti": 1024*1024, "K": 1/1000, "M": 1, "G": 1000}
    for suffix, factor in units.items():
        if mem_str.endswith(suffix):
            return float(mem_str[:-len(suffix)]) * factor
    return float(mem_str) / (1024 * 1024)


def get_idle_pods(namespace: str = None) -> list:
    """Return pods with zero CPU requests (likely idle/misconfigured)."""
    _load_config()
    v1 = client.CoreV1Api()
    pods = v1.list_pod_for_all_namespaces().items if not namespace else \
           v1.list_namespaced_pod(namespace).items

    idle = []
    for pod in pods:
        if pod.status.phase not in ("Running", "Pending"):
            continue
        total_cpu = sum(
            _parse_cpu(c.resources.requests.get("cpu", "0") if c.resources and c.resources.requests else "0")
            for c in (pod.spec.containers or [])
        )
        if total_cpu == 0:
            idle.append({
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "phase": pod.status.phase,
                "cpu_requests_m": total_cpu,
                "node": pod.spec.node_name,
            })
    return idle


def get_oversized_deployments(namespace: str = None) -> list:
    """Return deployments where replicas > 1 but avg CPU request is very low."""
    _load_config()
    apps = client.AppsV1Api()
    deps = apps.list_deployment_for_all_namespaces().items if not namespace else \
           apps.list_namespaced_deployment(namespace).items

    oversized = []
    for dep in deps:
        replicas = dep.spec.replicas or 1
        containers = dep.spec.template.spec.containers or []
        total_cpu = sum(
            _parse_cpu(c.resources.requests.get("cpu", "0") if c.resources and c.resources.requests else "0")
            for c in containers
        )
        if replicas > 2 and total_cpu < 100:  # >2 replicas but <100m CPU each
            oversized.append({
                "name": dep.metadata.name,
                "namespace": dep.metadata.namespace,
                "replicas": replicas,
                "cpu_requests_m": total_cpu,
                "recommendation": f"Scale down from {replicas} to 1-2 replicas",
            })
    return oversized


def get_node_summary() -> list:
    """Return node capacity and allocatable resources."""
    _load_config()
    v1 = client.CoreV1Api()
    nodes = []
    for node in v1.list_node().items:
        cap = node.status.capacity or {}
        alloc = node.status.allocatable or {}
        nodes.append({
            "name": node.metadata.name,
            "cpu_capacity": cap.get("cpu", "0"),
            "mem_capacity_mb": _parse_mem_mb(cap.get("memory", "0")),
            "cpu_allocatable": alloc.get("cpu", "0"),
            "mem_allocatable_mb": _parse_mem_mb(alloc.get("memory", "0")),
            "ready": any(
                c.type == "Ready" and c.status == "True"
                for c in (node.status.conditions or [])
            ),
        })
    return nodes


def scan_k8s_waste() -> list:
    """
    Returns a list of waste findings from Kubernetes.
    Each finding matches the WasteFinding schema used by the rest of the system.
    """
    from data.types import WasteFinding
    findings = []
    try:
        for pod in get_idle_pods():
            findings.append(WasteFinding(
                resource_id=f"k8s/{pod['namespace']}/{pod['name']}",
                waste_type="idle",
                monthly_cost=5.0,  # rough estimate per idle pod
                recommendation="Remove or configure resource requests",
                severity="medium",
            ))
        for dep in get_oversized_deployments():
            findings.append(WasteFinding(
                resource_id=f"k8s/{dep['namespace']}/{dep['name']}",
                waste_type="oversized",
                monthly_cost=dep["replicas"] * 10.0,
                recommendation=dep["recommendation"],
                severity="low",
            ))
    except Exception as e:
        print(f"[k8s] scan error: {e}")
    return findings


def is_available() -> bool:
    if not _K8S_AVAILABLE:
        return False
    try:
        _load_config()
        return True
    except Exception:
        return False
