import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from memory.store import record_outcome, get_similar_outcomes, get_approval_pattern, seed_memory, _MEMORY_FILE


def _cleanup():
    if _MEMORY_FILE.exists():
        _MEMORY_FILE.unlink()


def test_record_outcome_appends():
    _cleanup()
    record_outcome({"action_id": "t-001", "resource_type": "ec2", "action": "terminate", "accuracy": 0.9, "simulated_savings": 100.0, "actual_savings": 90.0, "approved": True})
    record_outcome({"action_id": "t-002", "resource_type": "ec2", "action": "terminate", "accuracy": 0.8, "simulated_savings": 50.0, "actual_savings": 40.0, "approved": False})
    data = json.loads(_MEMORY_FILE.read_text())
    assert len(data) == 2
    assert data[0]["action_id"] == "t-001"
    _cleanup()


def test_get_similar_outcomes_averages():
    _cleanup()
    seed_memory()
    # 3 ec2 terminate records: accuracies 1.0, 0.80, 0.90
    result = get_similar_outcomes("ec2", "terminate")
    assert result["count"] == 3
    assert abs(result["avg_accuracy"] - round((1.0 + 0.80 + 0.90) / 3, 4)) < 0.001
    _cleanup()


def test_get_approval_pattern():
    _cleanup()
    seed_memory()
    # resize: act-002 (approved=True), act-005 (approved=True), act-010 (approved=False) => 2/3
    result = get_approval_pattern("resize")
    assert result["count"] == 3
    assert abs(result["approve_rate"] - round(2 / 3, 4)) < 0.001
    _cleanup()


if __name__ == "__main__":
    test_record_outcome_appends()
    test_get_similar_outcomes_averages()
    test_get_approval_pattern()
    print("All memory tests passed.")
