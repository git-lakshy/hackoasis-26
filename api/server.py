import json
from pathlib import Path
from typing import List, Optional
from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.supervisor import run_cycle, resume_with_approval, chat as supervisor_chat
from data.mock_cloud import reset_state
from memory.store import seed_memory

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    # Initialize data files and seed memory on startup
    for f in ["action_log.json", "sim_cache.json"]:
        p = DATA / f
        if not p.exists() or p.read_text().strip() == "":
            p.write_text("[]")
    seed_memory()
    yield

app = FastAPI(title="FinOps AI Agent API", lifespan=lifespan)

# In-memory cycle state (single-user demo)
_state: dict = {}

DATA = Path(__file__).parent.parent / "data"


def _serialize(obj):
    """Recursively convert dataclasses/objects to dicts."""
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    if isinstance(obj, list):
        return [_serialize(i) for i in obj]
    if isinstance(obj, tuple):
        return [_serialize(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    return obj


# ── /run ──────────────────────────────────────────────────────────────────────

@app.post("/run")
def run():
    global _state
    _state = run_cycle()
    approval_queue = [
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
    executed = _serialize(_state.get("executed", []))
    return {
        "trace": _state.get("trace", []),
        "findings_count": len(_state.get("findings", [])),
        "opportunities_count": len(_state.get("opportunities", [])),
        "auto_executed": len(_state.get("executed", [])),
        "pending_approval": len(_state.get("approval_queue", [])),
        "approval_queue": approval_queue,
        "executed": executed,
    }


# ── /run/queue ────────────────────────────────────────────────────────────────

@app.get("/run/queue")
def get_queue():
    if not _state:
        raise HTTPException(400, "No cycle state. Run /run first.")
    approval_queue = [
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
    return {"approval_queue": approval_queue}


# ── /approve ──────────────────────────────────────────────────────────────────

class ApproveRequest(BaseModel):
    approved_ids: List[str]

@app.post("/approve")
def approve(req: ApproveRequest):
    global _state
    if not _state:
        raise HTTPException(400, "No cycle state. Run /run first.")
    # Pass approved_ids into existing in-memory state and re-invoke
    _state = resume_with_approval(_state, req.approved_ids)
    executed = _serialize(_state.get("executed", []))
    return {
        "trace": _state.get("trace", []),
        "executed": executed,
        "total_executed": len(executed),
    }


# ── /log ──────────────────────────────────────────────────────────────────────

@app.get("/log")
def get_log():
    log_file = DATA / "action_log.json"
    if not log_file.exists():
        return {"log": []}
    return {"log": json.loads(log_file.read_text())}


# ── /chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str

@app.post("/chat")
def chat(req: ChatRequest):
    response = supervisor_chat(req.query, _state)
    return {"response": response}


# ── /reset ────────────────────────────────────────────────────────────────────

@app.post("/reset")
def reset():
    global _state
    _state = {}
    reset_state()
    (DATA / "action_log.json").write_text("[]")
    (DATA / "sim_cache.json").write_text("[]")
    return {"status": "reset"}


# ── /status ───────────────────────────────────────────────────────────────────

@app.get("/status")
def status():
    return {
        "cycle_run": bool(_state),
        "findings": len(_state.get("findings", [])),
        "pending_approval": len(_state.get("approval_queue", [])),
        "executed": len(_state.get("executed", [])),
    }
