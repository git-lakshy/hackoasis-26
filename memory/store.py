import json
from pathlib import Path

_ROOT = Path(__file__).parent.parent
_MEMORY_FILE = _ROOT / "data" / "memory.json"


def _load() -> list:
    if not _MEMORY_FILE.exists():
        return []
    with open(_MEMORY_FILE) as f:
        return json.load(f)


def _save(data: list):
    _MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_outcome(action_record_dict: dict):
    data = _load()
    data.append(action_record_dict)
    _save(data)


def get_similar_outcomes(resource_type: str, action: str) -> dict:
    records = [
        r for r in _load()
        if r.get("resource_type") == resource_type and r.get("action") == action
        and r.get("accuracy") is not None
    ]
    if not records:
        return {"avg_accuracy": None, "avg_savings_delta": None, "count": 0}
    avg_accuracy = sum(r["accuracy"] for r in records) / len(records)
    avg_savings_delta = sum(
        r.get("actual_savings", 0) - r.get("simulated_savings", 0) for r in records
    ) / len(records)
    return {"avg_accuracy": round(avg_accuracy, 4), "avg_savings_delta": round(avg_savings_delta, 2), "count": len(records)}


def get_approval_pattern(action: str) -> dict:
    records = [r for r in _load() if r.get("action") == action]
    if not records:
        return {"approve_rate": None, "count": 0}
    approved = sum(1 for r in records if r.get("approved") is True)
    return {"approve_rate": round(approved / len(records), 4), "count": len(records)}


def seed_memory():
    records = [
        {"action_id": "act-001", "resource_id": "aws-ec2-idle-1", "resource_type": "ec2", "action": "terminate", "risk_tier": "low", "simulated_savings": 140.0, "actual_savings": 140.0, "accuracy": 1.0, "approved": True, "timestamp": "2026-04-01T10:00:00"},
        {"action_id": "act-002", "resource_id": "gcp-vm-oversized-1", "resource_type": "vm", "action": "resize", "risk_tier": "medium", "simulated_savings": 310.0, "actual_savings": 295.0, "accuracy": 0.95, "approved": True, "timestamp": "2026-04-03T11:00:00"},
        {"action_id": "act-003", "resource_id": "aws-rds-dev-1", "resource_type": "rds", "action": "schedule", "risk_tier": "low", "simulated_savings": 108.0, "actual_savings": 97.0, "accuracy": 0.90, "approved": True, "timestamp": "2026-04-05T09:00:00"},
        {"action_id": "act-004", "resource_id": "az-disk-orphan-1", "resource_type": "managed_disk", "action": "delete", "risk_tier": "low", "simulated_savings": 35.0, "actual_savings": 35.0, "accuracy": 1.0, "approved": True, "timestamp": "2026-04-07T14:00:00"},
        {"action_id": "act-005", "resource_id": "gcp-vm-oversized-2", "resource_type": "vm", "action": "resize", "risk_tier": "medium", "simulated_savings": 310.0, "actual_savings": 280.0, "accuracy": 0.90, "approved": True, "timestamp": "2026-04-10T10:30:00"},
        {"action_id": "act-006", "resource_id": "aws-ec2-idle-2", "resource_type": "ec2", "action": "terminate", "risk_tier": "low", "simulated_savings": 140.0, "actual_savings": 112.0, "accuracy": 0.80, "approved": False, "timestamp": "2026-04-12T16:00:00"},
        {"action_id": "act-007", "resource_id": "aws-rds-dev-2", "resource_type": "rds", "action": "schedule", "risk_tier": "low", "simulated_savings": 108.0, "actual_savings": 100.0, "accuracy": 0.93, "approved": True, "timestamp": "2026-04-14T08:00:00"},
        {"action_id": "act-008", "resource_id": "az-disk-orphan-2", "resource_type": "managed_disk", "action": "delete", "risk_tier": "low", "simulated_savings": 18.0, "actual_savings": 18.0, "accuracy": 1.0, "approved": True, "timestamp": "2026-04-16T13:00:00"},
        {"action_id": "act-009", "resource_id": "aws-ec2-idle-3", "resource_type": "ec2", "action": "terminate", "risk_tier": "low", "simulated_savings": 70.0, "actual_savings": 63.0, "accuracy": 0.90, "approved": True, "timestamp": "2026-04-18T11:00:00"},
        {"action_id": "act-010", "resource_id": "gcp-vm-oversized-3", "resource_type": "vm", "action": "resize", "risk_tier": "medium", "simulated_savings": 310.0, "actual_savings": 265.0, "accuracy": 0.85, "approved": False, "timestamp": "2026-04-20T15:00:00"},
    ]
    _save(records)
