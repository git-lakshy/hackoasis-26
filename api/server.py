import json
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.supervisor import run_cycle, resume_with_approval, chat as supervisor_chat
from data.mock_cloud import reset_state
from memory.store import seed_memory

DATA = Path(__file__).parent.parent / "data"
_state: dict = {}


@asynccontextmanager
async def lifespan(app):
    DATA.mkdir(exist_ok=True)
    for f in ["action_log.json", "sim_cache.json", "memory.json"]:
        p = DATA / f
        if not p.exists() or p.read_text().strip() in ("", "null"):
            p.write_text("[]")
    seed_memory()
    yield


app = FastAPI(title="FinOps AI Agent API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _serialize(obj):
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, (list, tuple)):
        return [_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


def _queue_items():
    return [
        {
            "resource_id": opp.resource_id,
            "action": opp.action,
            "estimated_savings": opp.estimated_savings,
            "composite_score": opp.composite_score,
            "risk_tier": risk.risk_tier,
            "risk_factors": risk.risk_factors,
            "projected_savings": sim.projected_savings,
            "confidence": sim.confidence,
        }
        for opp, sim, risk in _state.get("approval_queue", [])
    ]


@app.get("/")
def root():
    return {"status": "FinOps AI Agent API is live", "docs": "/docs", "health": "/status"}


@app.get("/status")
def status():
    return {
        "cycle_run": bool(_state),
        "findings": len(_state.get("findings", [])),
        "pending_approval": len(_state.get("approval_queue", [])),
        "executed": len(_state.get("executed", [])),
    }


@app.post("/run")
def run():
    global _state
    _state = run_cycle()
    return {
        "trace": _state.get("trace", []),
        "findings_count": len(_state.get("findings", [])),
        "opportunities_count": len(_state.get("opportunities", [])),
        "auto_executed": len(_state.get("executed", [])),
        "pending_approval": len(_state.get("approval_queue", [])),
        "approval_queue": _queue_items(),
        "executed": _serialize(_state.get("executed", [])),
    }


@app.get("/run/queue")
def get_queue():
    if not _state:
        raise HTTPException(400, "No cycle state. Run /run first.")
    return {"approval_queue": _queue_items()}


class ApproveRequest(BaseModel):
    approved_ids: List[str]


@app.post("/approve")
def approve(req: ApproveRequest):
    global _state
    if not _state:
        raise HTTPException(400, "No cycle state. Run /run first.")
    _state = resume_with_approval(_state, req.approved_ids)
    executed = _serialize(_state.get("executed", []))
    return {"trace": _state.get("trace", []), "executed": executed, "total_executed": len(executed)}


@app.get("/log")
def get_log():
    p = DATA / "action_log.json"
    return {"log": json.loads(p.read_text()) if p.exists() else []}


class ChatRequest(BaseModel):
    query: str


@app.post("/chat")
def chat(req: ChatRequest):
    return {"response": supervisor_chat(req.query, _state)}


@app.post("/reset")
def reset():
    global _state
    _state = {}
    reset_state()
    (DATA / "action_log.json").write_text("[]")
    (DATA / "sim_cache.json").write_text("[]")
    return {"status": "reset"}


# ── Kubernetes endpoints ───────────────────────────────────────────────────────

@app.get("/k8s/scan")
def k8s_scan():
    try:
        from data.k8s_connector import scan_k8s_waste, is_available
        if not is_available():
            return {"findings": [], "error": "Kubernetes not available (check KUBECONFIG)"}
        findings = scan_k8s_waste()
        return {"findings": [{"resource_id": f.resource_id, "waste_type": f.waste_type,
                               "monthly_cost": f.monthly_cost, "recommendation": f.recommendation,
                               "severity": f.severity} for f in findings]}
    except Exception as e:
        return {"findings": [], "error": str(e)}


@app.get("/k8s/nodes")
def k8s_nodes():
    try:
        from data.k8s_connector import get_node_summary, is_available
        if not is_available():
            return {"nodes": [], "error": "Kubernetes not available"}
        return {"nodes": get_node_summary()}
    except Exception as e:
        return {"nodes": [], "error": str(e)}


# ── Prometheus endpoints ───────────────────────────────────────────────────────

@app.get("/prometheus/idle")
def prometheus_idle():
    try:
        from data.prometheus_connector import get_idle_instances, is_available
        if not is_available():
            return {"idle_instances": [], "error": "Prometheus not reachable"}
        return {"idle_instances": get_idle_instances()}
    except Exception as e:
        return {"idle_instances": [], "error": str(e)}


@app.get("/prometheus/status")
def prometheus_status():
    import os
    from data.prometheus_connector import is_available
    url = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    return {"available": is_available(), "url": url}


# ── Terraform endpoints ────────────────────────────────────────────────────────

class TerraformRequest(BaseModel):
    resource_id: str
    action: str
    dry_run: bool = True
    region: str = "us-east-1"
    new_type: str = "t3.small"


@app.post("/terraform/plan")
def terraform_plan(req: TerraformRequest):
    try:
        from data.terraform_module import generate_and_apply, is_available
        if not is_available():
            return {"error": "terraform CLI not found in PATH"}
        result = generate_and_apply(
            req.resource_id, req.action,
            dry_run=req.dry_run,
            region=req.region,
            new_type=req.new_type,
        )
        return result
    except Exception as e:
        return {"error": str(e)}
