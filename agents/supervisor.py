from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Optional, Any

from agents.monitor_agent import run_monitor_scan
from agents.analyst_agent import run_analyst
from agents.optimizer_agent import run_optimizer
from agents.tradeoff_agent import run_tradeoff
from agents.simulation_agent import run_simulation
from agents.risk_agent import assess_risk, gate_actions
from agents.executor_agent import execute_batch
from data.mock_cloud import get_resources


class GraphState(TypedDict):
    findings: List[Any]
    opportunities: List[Any]
    simulations: List[Any]
    risks: List[Any]
    auto_queue: List[Any]
    approval_queue: List[Any]
    executed: List[Any]
    trace: List[str]
    approved_ids: Optional[List[str]]


def monitor_node(state: GraphState) -> GraphState:
    findings = run_monitor_scan()
    return {**state, "findings": findings, "trace": state["trace"] + [f"Monitor: {len(findings)} findings"]}


def analyst_node(state: GraphState) -> GraphState:
    findings = run_analyst(state["findings"])
    return {**state, "findings": findings, "trace": state["trace"] + [f"Analyst: {len(findings)} findings after analysis"]}


def optimizer_node(state: GraphState) -> GraphState:
    opportunities = run_optimizer(state["findings"])
    return {**state, "opportunities": opportunities, "trace": state["trace"] + [f"Optimizer: {len(opportunities)} opportunities"]}


def tradeoff_node(state: GraphState) -> GraphState:
    opportunities = run_tradeoff(state["opportunities"])
    return {**state, "opportunities": opportunities, "trace": state["trace"] + [f"Tradeoff: {len(opportunities)} opportunities ranked"]}


def simulator_node(state: GraphState) -> GraphState:
    simulations = run_simulation(state["opportunities"])
    return {**state, "simulations": simulations, "trace": state["trace"] + [f"Simulator: {len(simulations)} simulations"]}


def risk_node(state: GraphState) -> GraphState:
    opps, sims = state["opportunities"], state["simulations"]
    risks = [assess_risk(o, s) for o, s in zip(opps, sims)]
    return {**state, "risks": risks, "trace": state["trace"] + [f"Risk: {len(risks)} assessments"]}


def gate_node(state: GraphState) -> GraphState:
    result = gate_actions(state["opportunities"], state["simulations"], state["risks"])
    auto_q, appr_q = result["auto_queue"], result["approval_queue"]
    return {**state, "auto_queue": auto_q, "approval_queue": appr_q,
            "trace": state["trace"] + [f"Gate: {len(auto_q)} auto, {len(appr_q)} need approval"]}


def executor_node(state: GraphState) -> GraphState:
    approved_ids = state.get("approved_ids") or []
    queue = list(state["auto_queue"])
    for item in state["approval_queue"]:
        opp, sim, risk = item
        if opp.resource_id in approved_ids:
            queue.append(item)
    executed = execute_batch(queue)
    return {**state, "executed": executed, "trace": state["trace"] + [f"Executor: {len(executed)} actions executed"]}


def build_graph():
    g = StateGraph(GraphState)
    for name, fn in [
        ("monitor_node", monitor_node),
        ("analyst_node", analyst_node),
        ("optimizer_node", optimizer_node),
        ("tradeoff_node", tradeoff_node),
        ("simulator_node", simulator_node),
        ("risk_node", risk_node),
        ("gate_node", gate_node),
        ("executor_node", executor_node),
    ]:
        g.add_node(name, fn)

    g.set_entry_point("monitor_node")
    g.add_edge("monitor_node", "analyst_node")
    g.add_edge("analyst_node", "optimizer_node")
    g.add_edge("optimizer_node", "tradeoff_node")
    g.add_edge("tradeoff_node", "simulator_node")
    g.add_edge("simulator_node", "risk_node")
    g.add_edge("risk_node", "gate_node")
    g.add_edge("gate_node", "executor_node")
    g.add_edge("executor_node", END)

    return g.compile(interrupt_before=["executor_node"])


_EMPTY_STATE: GraphState = {
    "findings": [], "opportunities": [], "simulations": [], "risks": [],
    "auto_queue": [], "approval_queue": [], "executed": [], "trace": [], "approved_ids": None,
}

_graph = build_graph()


def run_cycle() -> dict:
    state = dict(_EMPTY_STATE)
    # Run all nodes except executor manually (avoid HITL complexity without checkpointer)
    state = monitor_node(state)
    state = analyst_node(state)
    state = optimizer_node(state)
    state = tradeoff_node(state)
    state = simulator_node(state)
    state = risk_node(state)
    state = gate_node(state)
    # Do NOT run executor_node yet — wait for approval
    return state


def resume_with_approval(state: dict, approved_ids: List[str]) -> dict:
    state["approved_ids"] = approved_ids
    return executor_node(state)


def chat(query: str, state: dict) -> str:
    q = query.lower()
    if not state or not state.get("findings"):
        return "Run an optimization cycle first to get insights."

    if any(k in q for k in ("waste", "cost", "expensive", "most")):
        findings = state.get("findings", [])
        top = sorted(findings, key=lambda f: f.monthly_cost, reverse=True)[:5]
        lines = [f"  {f.resource_id}: ${f.monthly_cost:.0f}/mo ({f.waste_type}, {f.root_cause})" for f in top]
        return f"Top {len(top)} cost wasters:\n" + "\n".join(lines)

    if any(k in q for k in ("risk", "approve", "pending")):
        queue = state.get("approval_queue", [])
        if not queue:
            return "No items pending approval."
        lines = [f"  {opp.resource_id}: {opp.action} (risk={risk.risk_tier}, save=${sim.projected_savings:.0f}/mo)"
                 for opp, sim, risk in queue[:5]]
        return f"{len(queue)} items need approval:\n" + "\n".join(lines)

    if any(k in q for k in ("saved", "executed", "done")):
        executed = state.get("executed", [])
        if not executed:
            return "No actions executed yet."
        total = sum(r.actual_savings or 0 for r in executed)
        lines = [f"  {r.resource_id}: {r.action} saved ${r.actual_savings or 0:.0f}/mo" for r in executed[:5]]
        return f"Executed {len(executed)} actions, ${total:.0f}/mo total savings:\n" + "\n".join(lines)

    opps = state.get("opportunities", [])
    if opps:
        total = sum(o.estimated_savings for o in opps)
        return f"Found {len(opps)} optimization opportunities worth ${total:.0f}/month. Try asking: 'what is wasting the most money?' or 'what needs approval?'"

    return "Run an optimization cycle first to get insights."
