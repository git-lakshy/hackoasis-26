# 🤖 Agent Architecture - Enhanced Design

**Project:** Agentic AI FinOps Platform  
**Version:** 2.0 (Production-Ready)  
**Last Updated:** May 15, 2026

---

## 🎯 Architecture Overview

The system uses a **multi-agent orchestration pattern** where specialized AI agents collaborate through a state machine to autonomously optimize cloud infrastructure costs while maintaining safety through human-in-the-loop approval for high-risk actions.

```
┌─────────────────────────────────────────────────────────────────┐
│                         SUPERVISOR                               │
│                    (LangGraph Orchestrator)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT PIPELINE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Monitor  │──▶│ Analyst  │──▶│Optimizer │──▶│Trade-off │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│       │              │               │               │           │
│       ▼              ▼               ▼               ▼           │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │Simulator │──▶│   Risk   │──▶│   Gate   │──▶│ Executor │    │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘    │
│                                      │               │           │
│                                      ▼               ▼           │
│                              ┌──────────────┐  ┌──────────┐    │
│                              │Approval Queue│  │Auto Queue│    │
│                              └──────────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │               │
                              ▼               ▼
                    ┌──────────────┐  ┌──────────────┐
                    │    Human     │  │   Memory     │
                    │   Approval   │  │    Store     │
                    └──────────────┘  └──────────────┘
```

---

## 🔄 Agent Pipeline Flow

### 1. Monitor Agent 📡
**Role:** Resource Discovery & Waste Detection  
**Input:** Cloud provider APIs (AWS, GCP, Azure)  
**Output:** List of `WasteFinding` objects

**Responsibilities:**
- Scan all cloud resources across providers
- Detect idle resources (CPU < 5%)
- Identify oversized instances (CPU < 20%)
- Find orphaned resources (unattached disks, unused LBs)
- Detect scheduling opportunities (dev resources running 24/7)

**Tools:**
- `scan_idle_resources(threshold)` - Find underutilized compute
- `scan_underutilized(threshold)` - Find oversized instances
- `scan_orphaned_resources()` - Find detached resources
- `get_cost_trend(resource_id)` - Historical cost analysis

**Enhanced Capabilities (v2.0):**
- Real-time CloudWatch/Cloud Monitoring integration
- Multi-region scanning
- Custom waste pattern definitions
- Anomaly detection for cost spikes

---

### 2. Analyst Agent 🔍
**Role:** Root Cause Analysis & Enrichment  
**Input:** `WasteFinding` list from Monitor  
**Output:** Enriched `WasteFinding` with root causes

**Responsibilities:**
- Analyze each finding for root cause
- Calculate accurate waste costs
- Compare against peer resources
- Classify severity (low/medium/high)

**Tools:**
- `analyze_resource(id)` - Deep resource analysis
- `calculate_waste_cost(id, type)` - Precise cost calculation
- `get_peer_comparison(id)` - Benchmark against similar resources
- `identify_root_cause(id, type)` - Root cause determination

**Root Cause Categories:**
- **Idle**: No active workload for 7+ days
- **Oversized**: Over-provisioned at launch
- **Orphaned**: Detached after workload migration
- **Scheduled**: Dev resource running outside business hours

**Enhanced Capabilities (v2.0):**
- ML-based pattern recognition
- Historical trend analysis
- Workload classification
- Cost attribution by team/project

---

### 3. Optimizer Agent ⚙️
**Role:** Opportunity Generation & Ranking  
**Input:** Enriched `WasteFinding` list  
**Output:** Ranked `OptimizationOpportunity` list

**Responsibilities:**
- Generate actionable optimization options
- Estimate savings for each action
- Score opportunities (cost, performance, availability)
- Rank by composite score

**Tools:**
- `generate_options(finding)` - Create action alternatives
- `estimate_savings(id, action)` - Calculate potential savings
- `rank_opportunities(opps)` - Sort by value

**Action Types:**
- **Resize**: Downsize instance type (50% cost reduction)
- **Schedule**: Run only during business hours (40% reduction)
- **Terminate**: Stop idle resources (100% reduction)
- **Delete**: Remove orphaned resources (100% reduction)

**Scoring Formula:**
```python
cost_score = min(savings / 1000 * 10, 10.0)
perf_score = action_impact_map[action]  # 5-9 scale
avail_score = base_score - env_penalty  # 0-10 scale
composite = cost * 0.4 + perf * 0.3 + avail * 0.3
```

**Enhanced Capabilities (v2.0):**
- Reserved Instance recommendations
- Savings Plans suggestions
- Spot instance opportunities
- Commitment-based discount analysis

---

### 4. Trade-off Agent ⚖️
**Role:** Multi-Objective Optimization  
**Input:** `OptimizationOpportunity` list  
**Output:** Scored opportunities with trade-off analysis

**Responsibilities:**
- Evaluate cost vs performance trade-offs
- Assess availability impact
- Calculate composite scores
- Re-rank by balanced value

**Scoring Dimensions:**
1. **Cost Impact** (40% weight)
   - Higher savings = higher score
   - Normalized to 0-10 scale

2. **Performance Impact** (30% weight)
   - Resize: 8/10 (minimal impact)
   - Schedule: 9/10 (no runtime impact)
   - Terminate: 5/10 (complete loss)
   - Delete: 7/10 (depends on resource)

3. **Availability Impact** (30% weight)
   - Environment penalty (prod: -3, dev: +1)
   - Action base score
   - Normalized to 0-10 scale

**Enhanced Capabilities (v2.0):**
- SLA compliance checking
- Business impact scoring
- Dependency analysis
- Rollback complexity assessment

---

### 5. Simulation Agent 🧪
**Role:** What-If Analysis & Projection  
**Input:** Ranked `OptimizationOpportunity` list  
**Output:** `SimulationResult` for each opportunity

**Responsibilities:**
- Project savings after action
- Estimate new utilization levels
- Calculate confidence scores
- Cache simulation results

**Simulation Models:**

**Resize:**
```python
projected_savings = current_cost * 0.5
projected_utilization = current_cpu * 1.8  # Workload on smaller instance
confidence = 0.85
time_to_savings = 7 days  # Instance replacement time
```

**Schedule:**
```python
projected_savings = current_cost * 0.4  # 60% uptime reduction
projected_utilization = current_cpu  # Same when running
confidence = 0.90
time_to_savings = 3 days  # Schedule setup time
```

**Terminate/Delete:**
```python
projected_savings = current_cost * 1.0  # Full cost elimination
projected_utilization = 0.0
confidence = 0.95
time_to_savings = 1 day  # Immediate
```

**Memory Augmentation:**
```python
# Adjust confidence based on historical accuracy
history = get_similar_outcomes(resource_type, action)
if history['count'] > 0:
    confidence *= history['avg_accuracy']
```

**Enhanced Capabilities (v2.0):**
- Monte Carlo simulations
- Sensitivity analysis
- Risk-adjusted projections
- Multi-scenario modeling

---

### 6. Risk Agent 🛡️
**Role:** Risk Assessment & Safety Gating  
**Input:** Opportunities + Simulations  
**Output:** `RiskAssessment` for each opportunity

**Responsibilities:**
- Calculate risk scores (0-100)
- Classify risk tiers (low/medium/high)
- Identify risk factors
- Gate high-risk actions for approval

**Risk Scoring Matrix:**

| Factor | Score | Condition |
|--------|-------|-----------|
| Production environment | +30 | env == 'prod' |
| Database resource | +25 | type in ['rds', 'database', 'sql'] |
| Terminate action | +20 | action == 'terminate' |
| Delete action | +15 | action == 'delete' |
| High savings | +10 | savings > $500/mo |
| Availability impact | +15 | availability_score < 5 |

**Risk Tiers:**
- **Low** (0-29): Auto-execute
- **Medium** (30-59): Auto-execute with logging
- **High** (60-100): Require human approval

**Memory Augmentation:**
```python
# Adjust tier based on approval patterns
pattern = get_approval_pattern(action)
if pattern['approve_rate'] < 0.3:
    tier = escalate_tier(tier)  # Bump up one level
```

**Enhanced Capabilities (v2.0):**
- Compliance rule checking
- SLA violation prediction
- Blast radius calculation
- Rollback difficulty scoring

---

### 7. Gate Agent 🚪
**Role:** Action Routing & Queue Management  
**Input:** Opportunities + Simulations + Risk Assessments  
**Output:** `auto_queue` and `approval_queue`

**Responsibilities:**
- Route low/medium risk to auto-execution
- Route high risk to approval queue
- Maintain queue state
- Track pending approvals

**Routing Logic:**
```python
for opp, sim, risk in zip(opportunities, simulations, risks):
    if risk.risk_tier == 'high':
        approval_queue.append((opp, sim, risk))
    else:
        auto_queue.append((opp, sim, risk))
```

**Enhanced Capabilities (v2.0):**
- Priority queuing
- Batch approval workflows
- Approval delegation
- Timeout handling

---

### 8. Executor Agent ⚡
**Role:** Action Execution & Verification  
**Input:** Auto queue + Approved items  
**Output:** `ActionRecord` list

**Responsibilities:**
- Execute approved optimizations
- Capture before/after state
- Verify actual savings
- Calculate accuracy
- Log to audit trail
- Record to memory store

**Execution Flow:**
```python
1. Capture before_state
2. Apply action (resize/schedule/terminate/delete)
3. Capture after_state
4. Calculate actual_savings
5. Calculate accuracy = actual / simulated
6. Create ActionRecord
7. Append to action_log.json
8. Record to memory.json for learning
```

**Action Implementation:**

**Resize:**
```python
update_resource(id, 
    monthly_cost=before_cost * 0.5,
    instance_type=smaller_type,
    status='running')
```

**Schedule:**
```python
update_resource(id,
    monthly_cost=before_cost * 0.6,
    status='scheduled',
    schedule='9am-6pm weekdays')
```

**Terminate:**
```python
update_resource(id,
    monthly_cost=0.0,
    status='stopped')
```

**Delete:**
```python
update_resource(id,
    monthly_cost=0.0,
    status='deleted')
```

**Enhanced Capabilities (v2.0):**
- Rollback support
- Dry-run mode
- Staged rollouts
- Canary deployments
- Automatic verification

---

## 🧠 Supervisor (Orchestrator)

**Role:** Pipeline Coordination & Chat Interface  
**Technology:** LangGraph state machine

**Responsibilities:**
- Orchestrate agent pipeline
- Manage state transitions
- Handle interrupts for approval
- Provide chat interface
- Track execution trace

**State Machine:**
```python
monitor → analyst → optimizer → tradeoff → 
simulator → risk → gate → [INTERRUPT] → executor → END
```

**Interrupt Point:**
- Before executor for high-risk items
- Allows human approval
- Resumes with approved IDs

**Chat Interface:**
Handles natural language queries:
- "What is wasting the most money?"
- "What needs approval?"
- "What have we saved?"
- "Show me pending actions"

**Enhanced Capabilities (v2.0):**
- Streaming responses
- Context-aware conversations
- Proactive recommendations
- Multi-turn dialogues

---

## 💾 Data Layer

### Resource Model
```python
Resource = {
    "id": str,              # Unique identifier
    "cloud": str,           # aws | gcp | azure
    "type": str,            # ec2 | vm | rds | disk | etc.
    "env": str,             # prod | staging | dev
    "region": str,          # Cloud region
    "monthly_cost": float,  # Current monthly cost
    "cpu_util": float,      # CPU utilization %
    "mem_util": float,      # Memory utilization %
    "status": str,          # running | stopped | unattached
    "tags": dict,           # Resource tags
    "last_active": str      # ISO timestamp
}
```

### Shared Types
```python
@dataclass
class WasteFinding:
    resource_id: str
    waste_type: str  # idle | oversized | orphaned | scheduled
    monthly_cost: float
    root_cause: str
    severity: str  # low | medium | high

@dataclass
class OptimizationOpportunity:
    resource_id: str
    action: str  # resize | schedule | terminate | delete
    estimated_savings: float
    cost_score: float
    perf_score: float
    availability_score: float
    composite_score: float

@dataclass
class SimulationResult:
    resource_id: str
    action: str
    projected_savings: float
    projected_utilization: float
    confidence: float
    time_to_savings_days: int

@dataclass
class RiskAssessment:
    resource_id: str
    action: str
    risk_score: int
    risk_tier: str  # low | medium | high
    risk_factors: List[str]

@dataclass
class ActionRecord:
    action_id: str
    resource_id: str
    action: str
    risk_tier: str
    simulated_savings: float
    actual_savings: float
    accuracy: float
    timestamp: str
    reasoning: str
    before_state: dict
    after_state: dict
```

### Memory Store
```python
# Record outcomes for learning
record_outcome(action_record)

# Get historical accuracy
get_similar_outcomes(resource_type, action)
# Returns: {avg_accuracy, avg_savings_delta, count}

# Get approval patterns
get_approval_pattern(action)
# Returns: {approve_rate, count}
```

---

## 🔄 Enhanced Agent Capabilities (v2.0)

### New Agents

#### 9. Anomaly Agent 🚨
**Role:** Cost Spike & Pattern Detection  
**Capabilities:**
- Detect unusual cost increases
- Identify usage pattern changes
- Alert on budget overruns
- Seasonal trend analysis

#### 10. Forecast Agent 📈
**Role:** Predictive Analytics  
**Capabilities:**
- 30/60/90 day cost forecasts
- Capacity planning
- Budget burn rate prediction
- Trend extrapolation

#### 11. Recommendation Agent 💡
**Role:** Strategic Optimization  
**Capabilities:**
- Reserved Instance recommendations
- Savings Plans analysis
- Spot instance opportunities
- Commitment-based discounts

#### 12. Policy Agent 📋
**Role:** Compliance & Governance  
**Capabilities:**
- Custom optimization rules
- Tagging enforcement
- Compliance checking
- Cost allocation policies

---

## 🎯 Agent Communication Protocol

### State Passing
Agents communicate through shared state dictionary:
```python
GraphState = {
    "findings": List[WasteFinding],
    "opportunities": List[OptimizationOpportunity],
    "simulations": List[SimulationResult],
    "risks": List[RiskAssessment],
    "auto_queue": List[Tuple],
    "approval_queue": List[Tuple],
    "executed": List[ActionRecord],
    "trace": List[str],
    "approved_ids": Optional[List[str]]
}
```

### Agent Interface
Each agent implements:
```python
def agent_node(state: GraphState) -> GraphState:
    # 1. Extract relevant data from state
    input_data = state["previous_agent_output"]
    
    # 2. Process with agent logic
    output_data = agent_logic(input_data)
    
    # 3. Update state and trace
    return {
        **state,
        "agent_output": output_data,
        "trace": state["trace"] + [f"Agent: {summary}"]
    }
```

---

## 🚀 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interfaces                         │
├─────────────────────────────────────────────────────────────┤
│  CLI (Go)  │  Dashboard (Streamlit)  │  API (FastAPI)      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
├─────────────────────────────────────────────────────────────┤
│  Supervisor  │  8 Core Agents  │  4 Enhanced Agents         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Data Layer                              │
├─────────────────────────────────────────────────────────────┤
│  Cloud Connectors  │  Memory Store  │  Cache  │  Database   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Cloud Providers                            │
├─────────────────────────────────────────────────────────────┤
│       AWS        │        GCP        │       Azure          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Performance Characteristics

| Agent | Avg Time | Max Resources | Memory |
|-------|----------|---------------|--------|
| Monitor | 0.8s | 1000+ | 50MB |
| Analyst | 0.5s | 1000+ | 30MB |
| Optimizer | 0.6s | 1000+ | 40MB |
| Trade-off | 0.4s | 1000+ | 20MB |
| Simulator | 0.7s | 1000+ | 35MB |
| Risk | 0.3s | 1000+ | 15MB |
| Gate | 0.1s | 1000+ | 10MB |
| Executor | 0.9s | 100/batch | 25MB |

**Total Pipeline:** ~5-7 seconds for 1000 resources

---

## 🔐 Security Considerations

### Agent Isolation
- Each agent runs in isolated context
- No direct state mutation
- Immutable data passing

### Approval Gating
- High-risk actions require human approval
- Audit trail for all actions
- Rollback capability

### Credential Management
- Cloud credentials stored securely
- No credentials in logs
- Rotation support

---

## 🎓 Design Patterns

### 1. Agent Pattern
Each agent is a specialized, autonomous unit with:
- Single responsibility
- Clear input/output contracts
- Stateless operation
- Tool-based capabilities

### 2. Pipeline Pattern
Sequential processing with:
- State accumulation
- Trace logging
- Error propagation
- Interrupt points

### 3. Memory Pattern
Learning from outcomes:
- Historical tracking
- Accuracy calibration
- Pattern recognition
- Continuous improvement

### 4. Human-in-the-Loop Pattern
Safety through approval:
- Risk-based gating
- Approval queues
- Resume capability
- Audit trails

---

**Next:** See TASKS.md for implementation roadmap
