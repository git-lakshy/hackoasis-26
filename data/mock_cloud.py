import copy

_ORIGINAL = [
    # --- AWS EC2 (4 idle: cpu_util < 5) ---
    {"id": "aws-ec2-idle-1", "cloud": "aws", "env": "prod", "type": "ec2", "instance_type": "m5.xlarge", "cpu_util": 2.1, "status": "running", "monthly_cost": 140.0},
    {"id": "aws-ec2-idle-2", "cloud": "aws", "env": "prod", "type": "ec2", "instance_type": "m5.xlarge", "cpu_util": 1.8, "status": "running", "monthly_cost": 140.0},
    {"id": "aws-ec2-idle-3", "cloud": "aws", "env": "staging", "type": "ec2", "instance_type": "m5.large", "cpu_util": 3.5, "status": "running", "monthly_cost": 70.0},
    {"id": "aws-ec2-idle-4", "cloud": "aws", "env": "dev", "type": "ec2", "instance_type": "m5.large", "cpu_util": 4.2, "status": "running", "monthly_cost": 70.0},
    # --- AWS EC2 (normal) ---
    {"id": "aws-ec2-1", "cloud": "aws", "env": "prod", "type": "ec2", "instance_type": "c5.2xlarge", "cpu_util": 62.0, "status": "running", "monthly_cost": 248.0},
    {"id": "aws-ec2-2", "cloud": "aws", "env": "prod", "type": "ec2", "instance_type": "c5.xlarge", "cpu_util": 55.0, "status": "running", "monthly_cost": 124.0},
    {"id": "aws-ec2-3", "cloud": "aws", "env": "prod", "type": "ec2", "instance_type": "r5.2xlarge", "cpu_util": 71.0, "status": "running", "monthly_cost": 362.0},
    {"id": "aws-ec2-4", "cloud": "aws", "env": "staging", "type": "ec2", "instance_type": "t3.medium", "cpu_util": 38.0, "status": "running", "monthly_cost": 30.0},
    {"id": "aws-ec2-5", "cloud": "aws", "env": "dev", "type": "ec2", "instance_type": "t3.small", "cpu_util": 22.0, "status": "running", "monthly_cost": 15.0},
    # --- AWS RDS (2 dev running 24/7) ---
    {"id": "aws-rds-dev-1", "cloud": "aws", "env": "dev", "type": "rds", "instance_type": "db.m5.large", "cpu_util": 8.0, "status": "running", "monthly_cost": 180.0, "schedule": "24/7"},
    {"id": "aws-rds-dev-2", "cloud": "aws", "env": "dev", "type": "rds", "instance_type": "db.m5.large", "cpu_util": 6.5, "status": "running", "monthly_cost": 180.0, "schedule": "24/7"},
    # --- AWS RDS (normal) ---
    {"id": "aws-rds-1", "cloud": "aws", "env": "prod", "type": "rds", "instance_type": "db.r5.xlarge", "cpu_util": 45.0, "status": "running", "monthly_cost": 480.0},
    {"id": "aws-rds-2", "cloud": "aws", "env": "prod", "type": "rds", "instance_type": "db.r5.large", "cpu_util": 38.0, "status": "running", "monthly_cost": 240.0},
    # --- AWS Load Balancers (2 unused) ---
    {"id": "aws-alb-unused-1", "cloud": "aws", "env": "staging", "type": "load_balancer", "requests_per_day": 0, "status": "active", "monthly_cost": 22.0, "targets": 0},
    {"id": "aws-alb-unused-2", "cloud": "aws", "env": "dev", "type": "load_balancer", "requests_per_day": 0, "status": "active", "monthly_cost": 22.0, "targets": 0},
    # --- AWS Load Balancers (normal) ---
    {"id": "aws-alb-1", "cloud": "aws", "env": "prod", "type": "load_balancer", "requests_per_day": 85000, "status": "active", "monthly_cost": 45.0, "targets": 6},
    {"id": "aws-alb-2", "cloud": "aws", "env": "prod", "type": "load_balancer", "requests_per_day": 42000, "status": "active", "monthly_cost": 35.0, "targets": 4},
    # --- AWS S3 ---
    {"id": "aws-s3-1", "cloud": "aws", "env": "prod", "type": "s3", "size_gb": 5000, "status": "active", "monthly_cost": 115.0},
    {"id": "aws-s3-2", "cloud": "aws", "env": "prod", "type": "s3", "size_gb": 2000, "status": "active", "monthly_cost": 46.0},
    {"id": "aws-s3-3", "cloud": "aws", "env": "dev", "type": "s3", "size_gb": 300, "status": "active", "monthly_cost": 7.0},
    # --- AWS Lambda ---
    {"id": "aws-lambda-1", "cloud": "aws", "env": "prod", "type": "lambda", "invocations_per_day": 50000, "status": "active", "monthly_cost": 18.0},
    {"id": "aws-lambda-2", "cloud": "aws", "env": "prod", "type": "lambda", "invocations_per_day": 12000, "status": "active", "monthly_cost": 5.0},

    # --- GCP VMs (3 oversized: cpu_util < 15, type=n2-standard-16) ---
    {"id": "gcp-vm-oversized-1", "cloud": "gcp", "env": "prod", "type": "vm", "instance_type": "n2-standard-16", "cpu_util": 9.0, "status": "running", "monthly_cost": 620.0},
    {"id": "gcp-vm-oversized-2", "cloud": "gcp", "env": "prod", "type": "vm", "instance_type": "n2-standard-16", "cpu_util": 11.5, "status": "running", "monthly_cost": 620.0},
    {"id": "gcp-vm-oversized-3", "cloud": "gcp", "env": "staging", "type": "vm", "instance_type": "n2-standard-16", "cpu_util": 13.2, "status": "running", "monthly_cost": 620.0},
    # --- GCP VMs (normal) ---
    {"id": "gcp-vm-1", "cloud": "gcp", "env": "prod", "type": "vm", "instance_type": "n2-standard-4", "cpu_util": 58.0, "status": "running", "monthly_cost": 155.0},
    {"id": "gcp-vm-2", "cloud": "gcp", "env": "prod", "type": "vm", "instance_type": "n2-standard-8", "cpu_util": 67.0, "status": "running", "monthly_cost": 310.0},
    {"id": "gcp-vm-3", "cloud": "gcp", "env": "staging", "type": "vm", "instance_type": "n2-standard-2", "cpu_util": 34.0, "status": "running", "monthly_cost": 78.0},
    {"id": "gcp-vm-4", "cloud": "gcp", "env": "dev", "type": "vm", "instance_type": "e2-medium", "cpu_util": 19.0, "status": "running", "monthly_cost": 25.0},
    # --- GCP Cloud SQL ---
    {"id": "gcp-sql-1", "cloud": "gcp", "env": "prod", "type": "cloud_sql", "instance_type": "db-n1-standard-4", "cpu_util": 52.0, "status": "running", "monthly_cost": 290.0},
    {"id": "gcp-sql-2", "cloud": "gcp", "env": "staging", "type": "cloud_sql", "instance_type": "db-n1-standard-2", "cpu_util": 28.0, "status": "running", "monthly_cost": 145.0},
    # --- GCP GKE ---
    {"id": "gcp-gke-1", "cloud": "gcp", "env": "prod", "type": "gke_cluster", "nodes": 6, "cpu_util": 61.0, "status": "running", "monthly_cost": 540.0},
    {"id": "gcp-gke-2", "cloud": "gcp", "env": "staging", "type": "gke_cluster", "nodes": 3, "cpu_util": 40.0, "status": "running", "monthly_cost": 270.0},
    # --- GCP Storage ---
    {"id": "gcp-storage-1", "cloud": "gcp", "env": "prod", "type": "gcs", "size_gb": 8000, "status": "active", "monthly_cost": 160.0},
    {"id": "gcp-storage-2", "cloud": "gcp", "env": "dev", "type": "gcs", "size_gb": 500, "status": "active", "monthly_cost": 10.0},
    # --- GCP Cloud Functions ---
    {"id": "gcp-func-1", "cloud": "gcp", "env": "prod", "type": "cloud_function", "invocations_per_day": 30000, "status": "active", "monthly_cost": 12.0},

    # --- Azure VMs ---
    {"id": "az-vm-1", "cloud": "azure", "env": "prod", "type": "vm", "instance_type": "Standard_D4s_v3", "cpu_util": 55.0, "status": "running", "monthly_cost": 280.0},
    {"id": "az-vm-2", "cloud": "azure", "env": "prod", "type": "vm", "instance_type": "Standard_D8s_v3", "cpu_util": 63.0, "status": "running", "monthly_cost": 560.0},
    {"id": "az-vm-3", "cloud": "azure", "env": "staging", "type": "vm", "instance_type": "Standard_D2s_v3", "cpu_util": 41.0, "status": "running", "monthly_cost": 140.0},
    {"id": "az-vm-4", "cloud": "azure", "env": "dev", "type": "vm", "instance_type": "Standard_B2s", "cpu_util": 17.0, "status": "running", "monthly_cost": 35.0},
    # --- Azure Disks (3 orphaned: status=unattached) ---
    {"id": "az-disk-orphan-1", "cloud": "azure", "env": "prod", "type": "managed_disk", "size_gb": 512, "status": "unattached", "monthly_cost": 35.0},
    {"id": "az-disk-orphan-2", "cloud": "azure", "env": "staging", "type": "managed_disk", "size_gb": 256, "status": "unattached", "monthly_cost": 18.0},
    {"id": "az-disk-orphan-3", "cloud": "azure", "env": "dev", "type": "managed_disk", "size_gb": 128, "status": "unattached", "monthly_cost": 9.0},
    # --- Azure Disks (normal) ---
    {"id": "az-disk-1", "cloud": "azure", "env": "prod", "type": "managed_disk", "size_gb": 1024, "status": "attached", "monthly_cost": 70.0},
    {"id": "az-disk-2", "cloud": "azure", "env": "prod", "type": "managed_disk", "size_gb": 512, "status": "attached", "monthly_cost": 35.0},
    # --- Azure SQL ---
    {"id": "az-sql-1", "cloud": "azure", "env": "prod", "type": "azure_sql", "instance_type": "GP_Gen5_4", "cpu_util": 48.0, "status": "running", "monthly_cost": 370.0},
    {"id": "az-sql-2", "cloud": "azure", "env": "staging", "type": "azure_sql", "instance_type": "GP_Gen5_2", "cpu_util": 22.0, "status": "running", "monthly_cost": 185.0},
    # --- Azure AKS ---
    {"id": "az-aks-1", "cloud": "azure", "env": "prod", "type": "aks_cluster", "nodes": 5, "cpu_util": 58.0, "status": "running", "monthly_cost": 490.0},
    # --- Azure Blob Storage ---
    {"id": "az-blob-1", "cloud": "azure", "env": "prod", "type": "blob_storage", "size_gb": 6000, "status": "active", "monthly_cost": 120.0},
    {"id": "az-blob-2", "cloud": "azure", "env": "dev", "type": "blob_storage", "size_gb": 400, "status": "active", "monthly_cost": 8.0},
    # --- Azure Functions ---
    {"id": "az-func-1", "cloud": "azure", "env": "prod", "type": "azure_function", "invocations_per_day": 25000, "status": "active", "monthly_cost": 10.0},
    # --- Azure App Service ---
    {"id": "az-app-1", "cloud": "azure", "env": "prod", "type": "app_service", "instance_type": "P2v3", "cpu_util": 44.0, "status": "running", "monthly_cost": 210.0},
    {"id": "az-app-2", "cloud": "azure", "env": "staging", "type": "app_service", "instance_type": "P1v3", "cpu_util": 30.0, "status": "running", "monthly_cost": 105.0},
    # --- Azure Load Balancer (normal) ---
    {"id": "az-lb-1", "cloud": "azure", "env": "prod", "type": "load_balancer", "requests_per_day": 60000, "status": "active", "monthly_cost": 40.0},
    # --- Azure Cosmos DB ---
    {"id": "az-cosmos-1", "cloud": "azure", "env": "prod", "type": "cosmos_db", "cpu_util": 35.0, "status": "running", "monthly_cost": 320.0},
    # --- AWS ElastiCache ---
    {"id": "aws-cache-1", "cloud": "aws", "env": "prod", "type": "elasticache", "instance_type": "cache.r6g.large", "cpu_util": 28.0, "status": "running", "monthly_cost": 130.0},
    # --- AWS EKS ---
    {"id": "aws-eks-1", "cloud": "aws", "env": "prod", "type": "eks_cluster", "nodes": 8, "cpu_util": 66.0, "status": "running", "monthly_cost": 720.0},
    # --- GCP BigQuery ---
    {"id": "gcp-bq-1", "cloud": "gcp", "env": "prod", "type": "bigquery", "status": "active", "monthly_cost": 95.0},
    # --- AWS CloudFront ---
    {"id": "aws-cdn-1", "cloud": "aws", "env": "prod", "type": "cloudfront", "status": "active", "monthly_cost": 55.0},
]

_STATE: list = copy.deepcopy(_ORIGINAL)


def get_resources(cloud=None, env=None, resource_type=None) -> list:
    results = _STATE
    if cloud:
        results = [r for r in results if r["cloud"] == cloud]
    if env:
        results = [r for r in results if r["env"] == env]
    if resource_type:
        results = [r for r in results if r["type"] == resource_type]
    return results


def get_resource(resource_id: str) -> dict | None:
    return next((r for r in _STATE if r["id"] == resource_id), None)


def update_resource(resource_id: str, **kwargs) -> bool:
    resource = get_resource(resource_id)
    if resource is None:
        return False
    resource.update(kwargs)
    return True


def reset_state():
    global _STATE
    _STATE = copy.deepcopy(_ORIGINAL)
