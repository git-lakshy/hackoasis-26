"""
Terraform automation module.
Generates and applies Terraform plans for approved cost optimizations.
Requires: terraform CLI in PATH
"""
import os
import json
import subprocess
import tempfile
from pathlib import Path

TERRAFORM_DIR = os.getenv("TERRAFORM_DIR", "./terraform")


def _run(cmd: list, cwd: str = None) -> tuple[int, str, str]:
    """Run a subprocess command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=120
    )
    return result.returncode, result.stdout, result.stderr


def is_available() -> bool:
    code, _, _ = _run(["terraform", "version"])
    return code == 0


# ── Template generators ───────────────────────────────────────────────────────

def _ec2_stop_template(resource_id: str, region: str = "us-east-1") -> str:
    return f"""
terraform {{
  required_providers {{
    aws = {{ source = "hashicorp/aws", version = "~> 5.0" }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}

resource "aws_instance" "{resource_id.replace('-', '_')}_stop" {{
  # Stopping instance {resource_id}
  # This is a no-op resource — actual stop is via null_resource below
}}

resource "null_resource" "stop_{resource_id.replace('-', '_')}" {{
  provisioner "local-exec" {{
    command = "aws ec2 stop-instances --instance-ids {resource_id} --region {region}"
  }}
}}
"""


def _ec2_resize_template(resource_id: str, new_type: str, region: str = "us-east-1") -> str:
    return f"""
terraform {{
  required_providers {{
    aws = {{ source = "hashicorp/aws", version = "~> 5.0" }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}

data "aws_instance" "target" {{
  instance_id = "{resource_id}"
}}

resource "null_resource" "resize_{resource_id.replace('-', '_')}" {{
  provisioner "local-exec" {{
    command = <<-EOT
      aws ec2 stop-instances --instance-ids {resource_id} --region {region}
      aws ec2 wait instance-stopped --instance-ids {resource_id} --region {region}
      aws ec2 modify-instance-attribute --instance-id {resource_id} --instance-type {{"Value": "{new_type}"}} --region {region}
      aws ec2 start-instances --instance-ids {resource_id} --region {region}
    EOT
  }}
}}
"""


def _rds_stop_template(resource_id: str, region: str = "us-east-1") -> str:
    return f"""
terraform {{
  required_providers {{
    aws = {{ source = "hashicorp/aws", version = "~> 5.0" }}
  }}
}}

provider "aws" {{
  region = "{region}"
}}

resource "null_resource" "stop_rds_{resource_id.replace('-', '_')}" {{
  provisioner "local-exec" {{
    command = "aws rds stop-db-instance --db-instance-identifier {resource_id} --region {region}"
  }}
}}
"""


TEMPLATES = {
    "stop": _ec2_stop_template,
    "resize": _ec2_resize_template,
    "stop_rds": _rds_stop_template,
}


# ── Core functions ────────────────────────────────────────────────────────────

def generate_plan(resource_id: str, action: str, **kwargs) -> dict:
    """
    Generate a Terraform plan for a given action.
    Returns {"plan_dir": str, "template": str, "dry_run": bool}
    """
    region = kwargs.get("region", os.getenv("AWS_REGION", "us-east-1"))

    if action == "stop":
        tf_code = _ec2_stop_template(resource_id, region)
    elif action == "resize":
        new_type = kwargs.get("new_type", "t3.small")
        tf_code = _ec2_resize_template(resource_id, new_type, region)
    elif action == "stop_rds":
        tf_code = _rds_stop_template(resource_id, region)
    else:
        return {"error": f"No Terraform template for action: {action}"}

    plan_dir = tempfile.mkdtemp(prefix=f"finops_{resource_id}_")
    tf_file = Path(plan_dir) / "main.tf"
    tf_file.write_text(tf_code)

    return {"plan_dir": plan_dir, "template": tf_code, "resource_id": resource_id, "action": action}


def run_plan(plan_dir: str) -> dict:
    """Run terraform init + plan in the given directory."""
    if not is_available():
        return {"error": "terraform not found in PATH"}

    code, out, err = _run(["terraform", "init", "-no-color"], cwd=plan_dir)
    if code != 0:
        return {"error": f"terraform init failed: {err}"}

    code, out, err = _run(["terraform", "plan", "-no-color", "-out=tfplan"], cwd=plan_dir)
    return {
        "success": code == 0,
        "output": out,
        "error": err if code != 0 else None,
        "plan_dir": plan_dir,
    }


def apply_plan(plan_dir: str) -> dict:
    """Apply a previously generated plan."""
    if not is_available():
        return {"error": "terraform not found in PATH"}

    code, out, err = _run(
        ["terraform", "apply", "-auto-approve", "-no-color", "tfplan"],
        cwd=plan_dir,
    )
    return {
        "success": code == 0,
        "output": out,
        "error": err if code != 0 else None,
    }


def generate_and_apply(resource_id: str, action: str, dry_run: bool = True, **kwargs) -> dict:
    """
    Full pipeline: generate template → plan → (optionally) apply.
    dry_run=True only plans, does not apply.
    """
    plan_info = generate_plan(resource_id, action, **kwargs)
    if "error" in plan_info:
        return plan_info

    plan_result = run_plan(plan_info["plan_dir"])
    if not plan_result.get("success"):
        return plan_result

    if dry_run:
        return {"dry_run": True, "plan": plan_result["output"], "plan_dir": plan_info["plan_dir"]}

    return apply_plan(plan_info["plan_dir"])
