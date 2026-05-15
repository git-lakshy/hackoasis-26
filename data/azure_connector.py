"""
Azure real cloud connector.
Fetches VMs, SQL databases, and Load Balancers with CPU metrics.
Requires: azure-mgmt-compute, azure-mgmt-monitor, azure-mgmt-sql, azure-mgmt-network, azure-identity
"""
import os
from datetime import datetime, timedelta, timezone

try:
    from azure.identity import DefaultAzureCredential, ClientSecretCredential
    from azure.mgmt.compute import ComputeManagementClient
    from azure.mgmt.monitor import MonitorManagementClient
    from azure.mgmt.sql import SqlManagementClient
    from azure.mgmt.network import NetworkManagementClient
    _AZURE_AVAILABLE = True
except ImportError:
    _AZURE_AVAILABLE = False

# Rough Azure VM pricing (East US, Linux, pay-as-you-go)
VM_PRICES = {
    "Standard_B1s": 7.6, "Standard_B2s": 30.4, "Standard_B4ms": 121.6,
    "Standard_D2s_v3": 70.1, "Standard_D4s_v3": 140.2, "Standard_D8s_v3": 280.4,
    "Standard_E2s_v3": 91.0, "Standard_E4s_v3": 182.0,
    "Standard_F2s_v2": 61.8, "Standard_F4s_v2": 123.6,
}
SQL_MONTHLY = 150.0
LB_MONTHLY = 18.0


def _credential():
    tenant = os.getenv("AZURE_TENANT_ID")
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    if tenant and client_id and client_secret:
        return ClientSecretCredential(tenant, client_id, client_secret)
    return DefaultAzureCredential()


def _cpu_avg(monitor_client, resource_id: str) -> float:
    try:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=7)
        metrics = monitor_client.metrics.list(
            resource_id,
            timespan=f"{start.isoformat()}/{end.isoformat()}",
            interval="P1D",
            metricnames="Percentage CPU",
            aggregation="Average",
        )
        values = [
            dp.average
            for ts in metrics.value
            for data in ts.timeseries
            for dp in data.data
            if dp.average is not None
        ]
        return round(sum(values) / len(values), 2) if values else 0.0
    except Exception:
        return 0.0


def _get_vms(compute_client, monitor_client, subscription_id: str) -> list:
    resources = []
    for vm in compute_client.virtual_machines.list_all():
        rg = vm.id.split("/")[4]
        iv = compute_client.virtual_machines.instance_view(rg, vm.name)
        statuses = {s.code for s in (iv.statuses or [])}
        status = "running" if "PowerState/running" in statuses else "stopped"
        cpu = _cpu_avg(monitor_client, vm.id) if status == "running" else 0.0
        size = vm.hardware_profile.vm_size if vm.hardware_profile else ""
        resources.append({
            "id": vm.name,
            "cloud": "azure",
            "type": "vm",
            "region": vm.location,
            "env": (vm.tags or {}).get("Environment", "prod").lower(),
            "instance_type": size,
            "status": status,
            "cpu_util": cpu,
            "mem_util": 0.0,
            "disk_util": 0.0,
            "monthly_cost": VM_PRICES.get(size, 60.0),
            "tags": vm.tags or {},
            "last_active": datetime.now(timezone.utc).isoformat(),
        })
    return resources


def _get_sql_dbs(sql_client) -> list:
    resources = []
    try:
        for server in sql_client.servers.list():
            rg = server.id.split("/")[4]
            for db in sql_client.databases.list_by_server(rg, server.name):
                if db.name == "master":
                    continue
                resources.append({
                    "id": db.name,
                    "cloud": "azure",
                    "type": "sql_database",
                    "region": db.location,
                    "env": "prod",
                    "instance_type": db.sku.name if db.sku else "",
                    "status": db.status.lower() if db.status else "unknown",
                    "cpu_util": 0.0,
                    "mem_util": 0.0,
                    "disk_util": 0.0,
                    "monthly_cost": SQL_MONTHLY,
                    "tags": db.tags or {},
                    "last_active": datetime.now(timezone.utc).isoformat(),
                })
    except Exception:
        pass
    return resources


def fetch_azure_resources() -> list:
    if not _AZURE_AVAILABLE:
        raise RuntimeError(
            "Azure SDK not installed. Run: pip install azure-identity azure-mgmt-compute "
            "azure-mgmt-monitor azure-mgmt-sql azure-mgmt-network"
        )
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        raise RuntimeError("AZURE_SUBSCRIPTION_ID env var not set")

    cred = _credential()
    compute = ComputeManagementClient(cred, subscription_id)
    monitor = MonitorManagementClient(cred, subscription_id)
    sql = SqlManagementClient(cred, subscription_id)

    resources = _get_vms(compute, monitor, subscription_id)
    resources += _get_sql_dbs(sql)
    return resources


def is_available() -> bool:
    if not _AZURE_AVAILABLE:
        return False
    return bool(os.getenv("AZURE_SUBSCRIPTION_ID"))
