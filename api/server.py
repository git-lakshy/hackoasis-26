import os
# Load .env FIRST — before any agent imports so GROQ_API_KEY, CLOUD_MODE, etc. are visible
from dotenv import load_dotenv
load_dotenv()

import json
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import List, Optional
import asyncio

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

# Also load credentials from CLI config if present (merges, doesn't overwrite .env)
_config_path = Path.home() / ".baburao" / "config.json"
if _config_path.exists():
    try:
        _cfg = json.loads(_config_path.read_text())
        for k, v in _cfg.items():
            if k not in os.environ:
                os.environ[k] = v
    except Exception:
        pass

from agents.supervisor import run_cycle, resume_with_approval, chat as supervisor_chat
from data.cloud_manager import reset_state, get_resources
from memory.store import seed_memory

DATA = Path(__file__).parent.parent / "data"
_state: dict = {}
API_VERSION = "1.0.0"


@asynccontextmanager
async def lifespan(app):
    DATA.mkdir(exist_ok=True)
    for f in ["action_log.json", "sim_cache.json", "memory.json"]:
        p = DATA / f
        if not p.exists() or p.read_text().strip() in ("", "null"):
            p.write_text("[]")
    seed_memory()
    yield


app = FastAPI(
    title="Baburao AI Agent API",
    version=API_VERSION,
    description="Autonomous AI-powered FinOps platform for cloud cost optimization",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# Pydantic Models
# ══════════════════════════════════════════════════════════════════════════════

class ApproveRequest(BaseModel):
    approved_ids: List[str]

class ChatRequest(BaseModel):
    query: str

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
    return {
        "name": "Baburao AI Agent API",
        "version": API_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "api_v1": "/api/v1"
    }


@app.get("/health")
def health():
    """Health check endpoint for load balancers"""
    return {"status": "healthy", "version": API_VERSION}


@app.get("/status")
def status():
    """Legacy status endpoint - use /api/v1/status instead"""
    return {
        "cycle_run": bool(_state),
        "findings": len(_state.get("findings", [])),
        "pending_approval": len(_state.get("approval_queue", [])),
        "executed": len(_state.get("executed", [])),
    }


# ══════════════════════════════════════════════════════════════════════════════
# API v1 Endpoints
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/api/v1/status")
def status_v1():
    """Get current optimization cycle status"""
    return {
        "version": API_VERSION,
        "cycle_run": bool(_state),
        "findings": len(_state.get("findings", [])),
        "opportunities": len(_state.get("opportunities", [])),
        "pending_approval": len(_state.get("approval_queue", [])),
        "auto_executed": len(_state.get("auto_queue", [])),
        "executed": len(_state.get("executed", [])),
        "trace": _state.get("trace", [])
    }


@app.get("/api/v1/resources")
def get_resources_v1(
    cloud: Optional[str] = Query(None, description="Filter by cloud provider (aws, gcp, azure)"),
    env: Optional[str] = Query(None, description="Filter by environment (prod, staging, dev)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type")
):
    """Get all cloud resources with optional filtering"""
    try:
        resources = get_resources(cloud=cloud, env=env, resource_type=resource_type)
        return {
            "count": len(resources),
            "resources": resources
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch resources: {str(e)}")


@app.get("/api/v1/opportunities")
def get_opportunities_v1(
    risk: Optional[str] = Query(None, description="Filter by risk tier (low, medium, high)"),
    min_savings: Optional[float] = Query(None, description="Minimum monthly savings")
):
    """Get optimization opportunities without running full cycle"""
    if not _state or not _state.get("opportunities"):
        raise HTTPException(400, "No opportunities available. Run /api/v1/run first.")
    
    opportunities = _state.get("opportunities", [])
    
    # Apply filters
    if risk:
        # Need to match with risk assessments
        filtered = []
        risks = {r.resource_id: r for r in _state.get("risks", [])}
        for opp in opportunities:
            if opp.resource_id in risks and risks[opp.resource_id].risk_tier == risk:
                filtered.append(opp)
        opportunities = filtered
    
    if min_savings:
        opportunities = [o for o in opportunities if o.estimated_savings >= min_savings]
    
    return {
        "count": len(opportunities),
        "opportunities": _serialize(opportunities)
    }


@app.post("/api/v1/run")
def run_v1():
    """Execute full optimization cycle (non-streaming)"""
    global _state
    _state = run_cycle()
    return {
        "version": API_VERSION,
        "trace": _state.get("trace", []),
        "findings_count": len(_state.get("findings", [])),
        "opportunities_count": len(_state.get("opportunities", [])),
        "auto_executed": len(_state.get("executed", [])),
        "pending_approval": len(_state.get("approval_queue", [])),
        "approval_queue": _queue_items(),
        "executed": _serialize(_state.get("executed", [])),
    }


@app.get("/api/v1/run/stream")
def run_v1_stream():
    """Execute optimization cycle with Server-Sent Events for real-time progress"""
    global _state
    events = []

    def progress_cb(agent: str, message: str):
        events.append(f"data: {json.dumps({'agent': agent, 'message': message})}\n\n")

    def generate():
        # We run synchronously and collect progress events
        import threading
        done = threading.Event()
        error_holder = []

        def run():
            global _state
            try:
                _state = run_cycle(progress_cb=progress_cb)
            except Exception as e:
                error_holder.append(str(e))
            finally:
                done.set()

        t = threading.Thread(target=run)
        t.start()

        sent = 0
        while not done.is_set() or sent < len(events):
            while sent < len(events):
                yield events[sent]
                sent += 1
            import time
            time.sleep(0.05)

        if error_holder:
            yield f"data: {json.dumps({'error': error_holder[0]})}\n\n"
        else:
            summary = {
                "done": True,
                "findings_count": len(_state.get("findings", [])),
                "opportunities_count": len(_state.get("opportunities", [])),
                "pending_approval": len(_state.get("approval_queue", [])),
                "approval_queue": _queue_items(),
            }
            yield f"data: {json.dumps(summary)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")



@app.get("/api/v1/queue")
def get_queue_v1():
    """Get approval queue"""
    if not _state:
        raise HTTPException(400, "No cycle state. Run /api/v1/run first.")
    return {
        "count": len(_state.get("approval_queue", [])),
        "approval_queue": _queue_items()
    }


@app.post("/api/v1/approve")
def approve_v1(req: ApproveRequest):
    """Approve and execute high-risk actions"""
    global _state
    if not _state:
        raise HTTPException(400, "No cycle state. Run /api/v1/run first.")
    _state = resume_with_approval(_state, req.approved_ids)
    executed = _serialize(_state.get("executed", []))
    return {
        "trace": _state.get("trace", []),
        "executed": executed,
        "total_executed": len(executed)
    }


@app.get("/api/v1/log")
def get_log_v1(
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    risk: Optional[str] = Query(None, description="Filter by risk tier"),
    action: Optional[str] = Query(None, description="Filter by action type")
):
    """Get action log with pagination and filtering"""
    p = DATA / "action_log.json"
    log = json.loads(p.read_text()) if p.exists() else []
    
    # Apply filters
    if risk:
        log = [entry for entry in log if entry.get("risk_tier") == risk]
    if action:
        log = [entry for entry in log if entry.get("action") == action]
    
    # Apply pagination
    total = len(log)
    log = log[offset:offset + limit]
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "count": len(log),
        "log": log
    }


@app.post("/api/v1/chat")
def chat_v1(req: ChatRequest):
    """Natural language interface to query the system"""
    return {
        "query": req.query,
        "response": supervisor_chat(req.query, _state)
    }


class RollbackRequest(BaseModel):
    action_id: str


@app.post("/api/v1/rollback")
def rollback_v1(req: RollbackRequest):
    """Rollback a previously executed action"""
    p = DATA / "action_log.json"
    if not p.exists():
        raise HTTPException(404, "No action log found")
    
    log = json.loads(p.read_text())
    action = next((a for a in log if a["action_id"] == req.action_id), None)
    
    if not action:
        raise HTTPException(404, f"Action {req.action_id} not found")
    
    # Restore before state
    from data.cloud_manager import update_resource
    before_state = action.get("before_state", {})
    resource_id = action["resource_id"]
    
    try:
        update_resource(resource_id, **before_state)
        return {
            "status": "rolled_back",
            "action_id": req.action_id,
            "resource_id": resource_id,
            "restored_state": before_state
        }
    except Exception as e:
        raise HTTPException(500, f"Rollback failed: {str(e)}")


@app.post("/api/v1/reset")
def reset_v1():
    """Reset demo state"""
    global _state
    _state = {}
    reset_state()
    (DATA / "action_log.json").write_text("[]")
    (DATA / "sim_cache.json").write_text("[]")
    return {"status": "reset", "version": API_VERSION}


@app.post("/api/v1/decide")
def decide_v1():
    """Run multi-agent debate for optimization decisions"""
    if not _state or not _state.get("opportunities"):
        raise HTTPException(400, "No opportunities available. Run /api/v1/run first.")
    
    try:
        from agents.debate_agent import run_debate_batch
        
        opportunities = _state.get("opportunities", [])
        simulations = _state.get("simulations", [])
        risks = _state.get("risks", [])
        
        # Run debates
        debates = run_debate_batch(opportunities, simulations, risks, use_llm=True)
        
        # Serialize results
        debate_results = []
        for debate in debates:
            debate_results.append({
                "resource_id": debate.resource_id,
                "original_action": debate.original_action,
                "debate_rounds": [[{
                    "agent_name": arg.agent_name,
                    "position": arg.position,
                    "reasoning": arg.reasoning,
                    "confidence": arg.confidence,
                    "alternative": arg.alternative
                } for arg in round_args] for round_args in debate.debate_rounds],
                "final_decision": debate.final_decision,
                "consensus_action": debate.consensus_action,
                "consensus_reasoning": debate.consensus_reasoning,
                "confidence": debate.confidence,
                "debate_summary": debate.debate_summary
            })
        
        return {
            "version": API_VERSION,
            "count": len(debate_results),
            "debates": debate_results
        }
    
    except ImportError:
        raise HTTPException(500, "Debate agent not available")
    except Exception as e:
        raise HTTPException(500, f"Debate failed: {str(e)}")


# ══════════════════════════════════════════════════════════════════════════════
# Legacy Endpoints (Deprecated - use /api/v1 instead)
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/run")
def run():
    """DEPRECATED: Use /api/v1/run instead"""
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
    """DEPRECATED: Use /api/v1/queue instead"""
    if not _state:
        raise HTTPException(400, "No cycle state. Run /run first.")
    return {"approval_queue": _queue_items()}


@app.post("/approve")
def approve(req: ApproveRequest):
    """DEPRECATED: Use /api/v1/approve instead"""
    global _state
    if not _state:
        raise HTTPException(400, "No cycle state. Run /run first.")
    _state = resume_with_approval(_state, req.approved_ids)
    executed = _serialize(_state.get("executed", []))
    return {"trace": _state.get("trace", []), "executed": executed, "total_executed": len(executed)}


@app.get("/log")
def get_log():
    """DEPRECATED: Use /api/v1/log instead"""
    p = DATA / "action_log.json"
    return {"log": json.loads(p.read_text()) if p.exists() else []}


@app.post("/chat")
def chat(req: ChatRequest):
    """DEPRECATED: Use /api/v1/chat instead"""
    return {"response": supervisor_chat(req.query, _state)}


@app.post("/reset")
def reset():
    """DEPRECATED: Use /api/v1/reset instead"""
    global _state
    _state = {}
    reset_state()
    (DATA / "action_log.json").write_text("[]")
    (DATA / "sim_cache.json").write_text("[]")
    return {"status": "reset"}


# ══════════════════════════════════════════════════════════════════════════════
# Kubernetes endpoints
# ══════════════════════════════════════════════════════════════════════════════

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
