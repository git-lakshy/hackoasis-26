import json
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
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
