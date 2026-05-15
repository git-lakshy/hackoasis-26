# agent.md — Intelligent Infrastructure Cost Optimizer
## Multi-Agent Coordination Document

**Status:** ✅ Phase 1 Complete (Mock Data) | 🚧 Phase 2 In Progress (Real Cloud Integration)

This document defines the coordination contracts for the multi-agent FinOps system. All agents communicate through shared data types and follow the pipeline orchestrated by the Supervisor.

**See also:**
- `CURRENT_STATUS.md` - Current project state and completed features
- `TASKS.md` - Detailed implementation roadmap for real cloud integration
- `AGENT_ARCHITECTURE.md` - Deep dive into agent design and capabilities

---

## Shared Data Contracts

### Resource Schema (`data/mock_cloud.py`)
```python
Resource = {
    "resource_id": str,       # e.g. "aws-ec2-001"
    "cloud": str,             # "aws" | "gcp" | "azure"
    "type": str,              # "ec2" | "vm" | "rds" | "disk" | "lb"
    "region": str,
    "env": str,               # "prod" | "staging" | "dev"
    "daily_cost": float,
    "cpu_util": float,        # 0-100
    "mem_util": float,        # 0-100
    "disk_util": float,       # 0-100
    "status": str,            # "running" | "stopped" | "idle" | "unattached"
    "tags": dict,
    "last_active": str        # ISO timestamp
}
```

### Shared Types (`data/types.py`)
```python
@dataclass class WasteFinding:
    resource_id, waste_type, monthly_cost, root_cause, severity

@dataclass class OptimizationOpportunity:
    resource_id, action, estimated_savings, cost_score, perf_score, availability_score, composite_score

@dataclass class SimulationResult:
    resource_id, action, projected_savings, projected_utilization, confidence, time_to_savings_days

@dataclass class RiskAssessment:
    resource_id, action, risk_score, risk_tier, risk_factors

@dataclass class ActionRecord:
    action_id, resource_id, action, risk_tier, simulated_savings, actual_savings, accuracy, timestamp, reasoning, before_state, after_state
```

### Canonical File Paths
```
data/types.py          — shared dataclasses
data/mock_cloud.py     — stateful resource store
data/action_log.json   — execution audit trail
data/memory.json       — outcome memory
data/sim_cache.json    — simulation cache
memory/store.py        — memory CRUD
notifications/notifier.py
agents/supervisor.py
app.py
```

---

## Sub-Agent A — Data Foundation
**Tasks 1, 12, 13 | Files: data/types.py, data/mock_cloud.py, memory/store.py**

### Task 1: Mock Data Layer
- `data/types.py`: all dataclasses above
- `data/mock_cloud.py`: ~60 resources (AWS/GCP/Azure), waste patterns seeded:
  - 4 idle EC2 (cpu_util < 5)
  - 3 oversized GCP VMs (cpu_util < 15, type=n2-standard-16)
  - 3 orphaned Azure disks (status=unattached)
  - 2 dev RDS running 24/7
  - 2 unused load balancers
  - Functions: `get_resources(cloud,env,resource_type)`, `get_resource(id)`, `update_resource(id,**kw)`, `reset_state()`
  - Total monthly spend ~$12,000–$15,000
- Init `data/action_log.json`, `data/memory.json`, `data/sim_cache.json` as `[]`
- `tests/test_mock_data.py`: assert 3 clouds, waste patterns detectable, update/reset works

### Task 12: Memory Store
- `memory/store.py`:
  - `record_outcome(action_record)` → append to memory.json
  - `get_similar_outcomes(resource_type, action) -> {avg_accuracy, avg_savings_delta, count}`
  - `get_approval_pattern(action) -> {approve_rate, count}`
  - `seed_memory()` → 10 historical outcomes (accuracies 80–95%)
- `tests/test_memory.py`: record 5, assert averages correct

### Task 13: Memory Augmentation Hooks
- `agents/simulation_agent.py`: adjust confidence via `get_similar_outcomes()`
- `agents/risk_agent.py`: nudge tier via `get_approval_pattern()`
- `agents/executor_agent.py`: call `record_outcome()` after verify

---

## Sub-Agent B — Detection Pipeline
**Tasks 2, 3, 4 | Files: agents/monitor_agent.py, analyst_agent.py, optimizer_agent.py**

### Task 2: Monitor Agent
- Tools: `scan_idle_resources(threshold=5.0)`, `scan_underutilized(threshold=20.0)`, `scan_orphaned_resources()`, `get_cost_trend(resource_id)`
- `create_monitor_agent()` → LangChain agent + ChatGroq(llama-3.3-70b-versatile)
- `run_monitor_scan() -> List[WasteFinding]`
- Fallback: if no GROQ_API_KEY, run tools directly without LLM

### Task 3: Analyst Agent
- Tools: `analyze_resource(id)`, `calculate_waste_cost(id)`, `get_peer_comparison(id)`, `identify_root_cause(id, waste_type)`
- `run_analyst(findings) -> List[WasteFinding]` (enriches with root_cause, monthly_cost)

### Task 4: Optimizer Agent
- Tools: `generate_options(finding)`, `estimate_savings(id, action)`, `rank_opportunities(opps)`
- Savings heuristics: resize=50% cost, schedule=40%, terminate=100%
- `run_optimizer(findings) -> List[OptimizationOpportunity]`

---

## Sub-Agent C — Evaluation Pipeline
**Tasks 5, 6, 7, 8 | Files: agents/tradeoff_agent.py, simulation_agent.py, risk_agent.py, executor_agent.py**

### Task 5: Trade-off Agent
- `score_cost_impact`, `score_performance_impact`, `score_availability_impact` → 0–10 each
- Composite = cost*0.4 + perf*0.3 + avail*0.3
- `run_tradeoff(opportunities) -> List[OptimizationOpportunity]`

### Task 6: Simulation Agent
- `simulate_action(opp) -> SimulationResult`: resize→50% savings/1.8x util/0.85 conf, schedule→40%/0.90, terminate→100%/0.95
- Cache to `data/sim_cache.json`
- `run_simulation(opportunities) -> List[SimulationResult]`
- Memory hook slot: `# MEMORY_HOOK: adjust confidence`

### Task 7: Risk Agent
- Risk scoring: is_prod+30, is_database+25, terminate+20, delete+15, savings>500+10, avail_score<5+15
- Tiers: <30=low, 30–60=medium, >60=high
- `gate_actions(assessments) -> {auto_queue, approval_queue}`
- Memory hook slot: `# MEMORY_HOOK: adjust tier`

### Task 8: Executor Agent
- `execute_action(opp, risk) -> ActionRecord`: before→apply→after→verify→log
- Apply: resize→daily_cost*0.5, schedule→status=scheduled, terminate→status=stopped
- `execute_batch(auto_queue, simulations, risks) -> List[ActionRecord]`
- Memory hook slot: `# MEMORY_HOOK: record_outcome`

---

## Sub-Agent D — UI + Orchestration
**Tasks 14, 10, 9, 11 | Files: notifications/notifier.py, app.py, agents/supervisor.py, README.md, requirements.txt, .env.example**

### Task 14: Notifier
- `SlackNotifier.send(opp, risk, sim, tradeoff)` → POST to SLACK_WEBHOOK_URL (skip if unset)
- `EmailNotifier.send(...)` → smtplib HTML email (skip if unset)
- `notify_approval_required(opp, risk, sim, tradeoff)` → calls both

### Task 10: Streamlit Dashboard
- Sidebar: Run Cycle button, cloud filter, Reset Demo button
- Tab 1: Cost Overview (Plotly bar chart by cloud, KPIs)
- Tab 2: Agent Trace (st.expander per agent)
- Tab 3: Action Log (st.dataframe with risk badges)
- Tab 4: Approval Queue (cards + Approve/Reject buttons)
- Tab 5: Chat (st.chat_input → supervisor.chat())
- st.session_state: graph_state, approval_queue, trace, messages

### Task 9: Supervisor (LangGraph)
- StateGraph nodes: monitor→analyst→optimizer→tradeoff→simulator→risk→gate→executor
- interrupt_before executor for high-risk items
- `run_cycle() -> dict`
- `resume_with_approval(state, approved_ids) -> dict`
- `chat(query, state) -> str`

### Task 11: Polish
- demo_mode flag seeds memory + dramatic scenario
- README.md with mermaid diagram + 3-command setup + 2-min demo script
- requirements.txt (pinned), .env.example
