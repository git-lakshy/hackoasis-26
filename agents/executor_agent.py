import json
import uuid
import datetime
from pathlib import Path
from typing import List
from data.types import OptimizationOpportunity, SimulationResult, RiskAssessment, ActionRecord
from data.mock_cloud import get_resource, update_resource
from memory.store import record_outcome

_LOG = Path(__file__).parent.parent / 'data' / 'action_log.json'


def execute_action(opp: OptimizationOpportunity, sim: SimulationResult, risk: RiskAssessment) -> ActionRecord:
    rid = opp.resource_id
    before_state = dict(get_resource(rid) or {"monthly_cost": 0})

    if opp.action == 'resize':
        update_resource(rid, monthly_cost=before_state['monthly_cost'] * 0.5, status='running')
    elif opp.action == 'schedule':
        update_resource(rid, monthly_cost=before_state['monthly_cost'] * 0.6, status='scheduled')
    elif opp.action == 'terminate':
        update_resource(rid, monthly_cost=0.0, status='stopped')
    elif opp.action == 'delete':
        update_resource(rid, monthly_cost=0.0, status='deleted')

    after_state = dict(get_resource(rid) or {"monthly_cost": 0})
    actual_savings = before_state['monthly_cost'] - after_state['monthly_cost']
    accuracy = actual_savings / sim.projected_savings if sim.projected_savings > 0 else None

    record = ActionRecord(
        action_id=str(uuid.uuid4())[:8],
        resource_id=rid,
        action=opp.action,
        risk_tier=risk.risk_tier,
        simulated_savings=sim.projected_savings,
        actual_savings=actual_savings,
        accuracy=accuracy,
        timestamp=datetime.datetime.utcnow().isoformat(),
        reasoning=f'Risk factors: {risk.risk_factors}. Composite score: {opp.composite_score:.1f}',
        before_state=before_state,
        after_state=after_state,
    )

    log = []
    if _LOG.exists():
        log = json.loads(_LOG.read_text())
    log.append(record.__dict__)
    _LOG.parent.mkdir(parents=True, exist_ok=True)
    _LOG.write_text(json.dumps(log, indent=2))
    record_outcome(record.__dict__)

    # Push metric to Prometheus Pushgateway (non-blocking)
    try:
        from data.prometheus_connector import push_optimization_metric
        push_optimization_metric(opp.action, actual_savings, rid)
    except Exception:
        pass

    return record


def execute_batch(auto_queue) -> List[ActionRecord]:
    executed = [execute_action(opp, sim, risk) for opp, sim, risk in auto_queue]

    # Send Slack summary after batch execution
    if executed:
        try:
            from notifications.notifier import notify_execution_summary
            notify_execution_summary([r.__dict__ for r in executed])
        except Exception:
            pass

    return executed
