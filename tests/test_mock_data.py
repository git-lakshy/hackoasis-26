import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from data.mock_cloud import get_resources, get_resource, update_resource, reset_state


def test_all_clouds_present():
    resources = get_resources()
    clouds = {r["cloud"] for r in resources}
    assert "aws" in clouds
    assert "gcp" in clouds
    assert "azure" in clouds


def test_idle_resources_detectable():
    resources = get_resources()
    idle = [r for r in resources if r.get("cpu_util", 100) < 5]
    assert len(idle) >= 4  # 4 seeded idle EC2s


def test_update_resource_mutates_state():
    reset_state()
    original = get_resource("aws-ec2-idle-1")
    assert original["cpu_util"] == 2.1
    update_resource("aws-ec2-idle-1", cpu_util=99.0, status="stopped")
    updated = get_resource("aws-ec2-idle-1")
    assert updated["cpu_util"] == 99.0
    assert updated["status"] == "stopped"


def test_reset_state_restores_original():
    update_resource("aws-ec2-idle-1", cpu_util=99.0)
    reset_state()
    restored = get_resource("aws-ec2-idle-1")
    assert restored["cpu_util"] == 2.1


if __name__ == "__main__":
    test_all_clouds_present()
    test_idle_resources_detectable()
    test_update_resource_mutates_state()
    test_reset_state_restores_original()
    print("All tests passed.")
