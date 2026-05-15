"""
Unified Cloud Resource Manager
Replaces mock_cloud.py with real cloud integrations
"""

import os
from typing import List, Dict, Optional

# Try to import cloud connectors
try:
    from data.aws_connector import fetch_aws_resources, is_available as aws_available
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    from data.gcp_connector import fetch_gcp_resources, is_available as gcp_available
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

try:
    from data.azure_connector import fetch_azure_resources, is_available as azure_available
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False

try:
    from data.k8s_connector import scan_k8s_waste, is_available as k8s_available
    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False

try:
    from data.prometheus_connector import enrich_resources_with_prometheus
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


# In-memory cache for resources
_RESOURCE_CACHE: Dict[str, dict] = {}
_CACHE_ENABLED = True


def get_resources(cloud: Optional[str] = None, env: Optional[str] = None, resource_type: Optional[str] = None) -> List[dict]:
    """
    Fetch resources from all available cloud providers.
    
    Args:
        cloud: Filter by cloud provider (aws, gcp, azure, k8s)
        env: Filter by environment (prod, staging, dev)
        resource_type: Filter by resource type
    
    Returns:
        List of resource dictionaries
    """
    resources = []
    
    # Fetch from AWS
    if (not cloud or cloud == "aws") and AWS_AVAILABLE:
        try:
            if aws_available():
                aws_resources = fetch_aws_resources()
                resources.extend(aws_resources)
                print(f"[CloudManager] Fetched {len(aws_resources)} AWS resources")
        except Exception as e:
            print(f"[CloudManager] AWS fetch failed: {e}")
    
    # Fetch from GCP
    if (not cloud or cloud == "gcp") and GCP_AVAILABLE:
        try:
            if gcp_available():
                gcp_resources = fetch_gcp_resources()
                resources.extend(gcp_resources)
                print(f"[CloudManager] Fetched {len(gcp_resources)} GCP resources")
        except Exception as e:
            print(f"[CloudManager] GCP fetch failed: {e}")
    
    # Fetch from Azure
    if (not cloud or cloud == "azure") and AZURE_AVAILABLE:
        try:
            if azure_available():
                azure_resources = fetch_azure_resources()
                resources.extend(azure_resources)
                print(f"[CloudManager] Fetched {len(azure_resources)} Azure resources")
        except Exception as e:
            print(f"[CloudManager] Azure fetch failed: {e}")
    
    # Fetch from Kubernetes
    if (not cloud or cloud == "k8s") and K8S_AVAILABLE:
        try:
            if k8s_available():
                k8s_findings = scan_k8s_waste()
                # Convert findings to resource format
                for finding in k8s_findings:
                    resources.append({
                        "id": finding.resource_id,
                        "cloud": "k8s",
                        "type": "pod" if "pod" in finding.resource_id else "deployment",
                        "env": "unknown",
                        "monthly_cost": finding.monthly_cost,
                        "cpu_util": 0.0,
                        "status": "running",
                        "waste_type": finding.waste_type,
                        "recommendation": finding.recommendation
                    })
                print(f"[CloudManager] Fetched {len(k8s_findings)} K8s resources")
        except Exception as e:
            print(f"[CloudManager] K8s fetch failed: {e}")
    
    # Enrich with Prometheus metrics if available
    if PROMETHEUS_AVAILABLE and resources:
        try:
            resources = enrich_resources_with_prometheus(resources)
            print(f"[CloudManager] Enriched resources with Prometheus metrics")
        except Exception as e:
            print(f"[CloudManager] Prometheus enrichment failed: {e}")
    
    # Update cache
    if _CACHE_ENABLED:
        for r in resources:
            _RESOURCE_CACHE[r["id"]] = r
    
    # Apply filters
    if env:
        resources = [r for r in resources if r.get("env") == env]
    if resource_type:
        resources = [r for r in resources if r.get("type") == resource_type]
    
    return resources


def get_resources_live(cloud: Optional[str] = None, env: Optional[str] = None, resource_type: Optional[str] = None) -> List[dict]:
    """Alias for get_resources for backward compatibility"""
    return get_resources(cloud, env, resource_type)


def get_resource(resource_id: str) -> Optional[dict]:
    """
    Get a single resource by ID.
    First checks cache, then fetches if not found.
    """
    # Check cache first
    if resource_id in _RESOURCE_CACHE:
        return _RESOURCE_CACHE[resource_id]
    
    # Fetch all resources and find the one we need
    resources = get_resources()
    for r in resources:
        if r["id"] == resource_id:
            return r
    
    return None


def update_resource(resource_id: str, **kwargs) -> bool:
    """
    Update a resource in the cache.
    Note: This only updates the cache, not the actual cloud resource.
    For real updates, use the appropriate cloud connector's update function.
    """
    if resource_id not in _RESOURCE_CACHE:
        # Try to fetch it first
        resource = get_resource(resource_id)
        if not resource:
            return False
    
    _RESOURCE_CACHE[resource_id].update(kwargs)
    return True


def reset_state():
    """Clear the resource cache"""
    global _RESOURCE_CACHE
    _RESOURCE_CACHE = {}
    print("[CloudManager] Resource cache cleared")


def get_available_clouds() -> List[str]:
    """Return list of available cloud providers"""
    clouds = []
    if AWS_AVAILABLE and aws_available():
        clouds.append("aws")
    if GCP_AVAILABLE and gcp_available():
        clouds.append("gcp")
    if AZURE_AVAILABLE and azure_available():
        clouds.append("azure")
    if K8S_AVAILABLE and k8s_available():
        clouds.append("k8s")
    return clouds


def get_cloud_status() -> Dict[str, dict]:
    """Get status of all cloud connectors"""
    status = {}
    
    if AWS_AVAILABLE:
        status["aws"] = {
            "available": aws_available(),
            "configured": bool(os.getenv("AWS_ACCESS_KEY_ID"))
        }
    else:
        status["aws"] = {"available": False, "configured": False, "error": "boto3 not installed"}
    
    if GCP_AVAILABLE:
        status["gcp"] = {
            "available": gcp_available(),
            "configured": bool(os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
        }
    else:
        status["gcp"] = {"available": False, "configured": False, "error": "google-cloud libraries not installed"}
    
    if AZURE_AVAILABLE:
        status["azure"] = {
            "available": azure_available(),
            "configured": bool(os.getenv("AZURE_SUBSCRIPTION_ID"))
        }
    else:
        status["azure"] = {"available": False, "configured": False, "error": "azure libraries not installed"}
    
    if K8S_AVAILABLE:
        status["k8s"] = {
            "available": k8s_available(),
            "configured": bool(os.getenv("KUBECONFIG") or os.path.exists(os.path.expanduser("~/.kube/config")))
        }
    else:
        status["k8s"] = {"available": False, "configured": False, "error": "kubernetes library not installed"}
    
    return status
