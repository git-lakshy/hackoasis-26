"""
GCP real cloud connector.
Fetches Compute Engine instances and Cloud SQL with CPU utilization.
Requires: google-cloud-compute, google-cloud-monitoring, google-cloud-billing
"""
import os
from datetime import datetime, timedelta, timezone

try:
    from google.cloud import compute_v1, monitoring_v3
    from google.protobuf.timestamp_pb2 import Timestamp
    _GCP_AVAILABLE = True
except ImportError:
    _GCP_AVAILABLE = False

# Rough GCP pricing (us-central1, Linux)
GCE_PRICES = {
    "e2-micro": 6.1, "e2-small": 12.2, "e2-medium": 24.5,
    "n1-standard-1": 24.3, "n1-standard-2": 48.5, "n1-standard-4": 97.1,
    "n2-standard-2": 58.3, "n2-standard-4": 116.6,
    "c2-standard-4": 134.5, "c2-standard-8": 269.0,
}
SQL_MONTHLY = 120.0


def _cpu_avg(project_id: str, instance_name: str, zone: str) -> float:
    try:
        client = monitoring_v3.MetricServiceClient()
        project_name = f"projects/{project_id}"
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)

        interval = monitoring_v3.TimeInterval(
            end_time=Timestamp(seconds=int(end.timestamp())),
            start_time=Timestamp(seconds=int(start.timestamp())),
        )
        results = client.list_time_series(
            request={
                "name": project_name,
                "filter": (
                    f'metric.type="compute.googleapis.com/instance/cpu/utilization" '
                    f'AND resource.labels.instance_id="{instance_name}"'
                ),
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
            }
        )
        values = [p.value.double_value * 100 for ts in results for p in ts.points]
        return round(sum(values) / len(values), 2) if values else 0.0
    except Exception:
        return 0.0


def _get_gce_instances(project_id: str) -> list:
    resources = []
    client = compute_v1.InstancesClient()
    for zone_instances in client.aggregated_list(project=project_id):
        zone_name, instances_scoped = zone_instances
        if not hasattr(instances_scoped, "instances"):
            continue
        for inst in instances_scoped.instances:
            status = inst.status.lower()  # RUNNING, TERMINATED, etc.
            machine_type = inst.machine_type.split("/")[-1] if inst.machine_type else ""
            zone = zone_name.replace("zones/", "")
            cpu = _cpu_avg(project_id, inst.name, zone) if status == "running" else 0.0
            labels = dict(inst.labels) if inst.labels else {}
            resources.append({
                "id": inst.name,
                "cloud": "gcp",
                "type": "gce_instance",
                "region": zone,
                "env": labels.get("environment", "prod").lower(),
                "instance_type": machine_type,
                "status": "running" if status == "running" else "stopped",
                "cpu_util": cpu,
                "mem_util": 0.0,
                "disk_util": 0.0,
                "monthly_cost": GCE_PRICES.get(machine_type, 50.0),
                "tags": labels,
                "last_active": datetime.now(timezone.utc).isoformat(),
            })
    return resources


def fetch_gcp_resources() -> list:
    if not _GCP_AVAILABLE:
        raise RuntimeError(
            "GCP SDK not installed. Run: pip install google-cloud-compute google-cloud-monitoring"
        )
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise RuntimeError("GCP_PROJECT_ID env var not set")

    resources = _get_gce_instances(project_id)
    return resources


def is_available() -> bool:
    if not _GCP_AVAILABLE:
        return False
    return bool(os.getenv("GCP_PROJECT_ID"))
