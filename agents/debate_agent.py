"""
Multi-Agent Debate System for Consensus-Based Decision Making

Agents argue about optimization decisions from different perspectives:
- Cost Agent: Focuses on maximum savings
- Risk Agent: Focuses on safety and availability
- Performance Agent: Focuses on workload requirements
- Scheduler Agent: Proposes timing-based compromises
- Consensus Agent: Synthesizes arguments and makes final decision
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field
from data.types import OptimizationOpportunity, SimulationResult, RiskAssessment
from data.cloud_manager import get_resource
import os

# Load .env so GROQ_API_KEY is visible at import time
from dotenv import load_dotenv
load_dotenv()

try:
    from langchain_groq import ChatGroq
    from langchain.schema import HumanMessage, SystemMessage
    GROQ_AVAILABLE = bool(os.getenv("GROQ_API_KEY"))
except ImportError:
    GROQ_AVAILABLE = False


@dataclass
class AgentArgument:
    agent_name: str
    position: str  # "support" | "oppose" | "compromise"
    reasoning: str
    confidence: float  # 0.0 - 1.0
    alternative: str = ""  # Alternative suggestion if opposing


@dataclass
class DebateResult:
    resource_id: str
    original_action: str
    debate_rounds: List[List[AgentArgument]]
    final_decision: str  # "approved" | "rejected" | "modified"
    consensus_action: str  # Final action to take
    consensus_reasoning: str
    confidence: float
    debate_summary: str


def _get_llm():
    """Get LLM instance if available"""
    if not GROQ_AVAILABLE:
        return None
    try:
        return ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=500
        )
    except Exception:
        return None

def _llm_argue(agent_name: str, agent_goal: str, opp: OptimizationOpportunity, sim: SimulationResult, risk: RiskAssessment, resource: dict) -> AgentArgument:
    llm = _get_llm()
    if not llm:
        return None
    
    prompt = f"""You are {agent_name}. Your primary goal is: {agent_goal}.
Analyze this proposed infrastructure optimization:
Resource: {opp.resource_id} (Type: {resource.get('type')}, Env: {resource.get('env')})
Action: {opp.action}
Projected Savings: ${sim.projected_savings:.0f}/mo
Risk Tier: {risk.risk_tier}
Risk Factors: {', '.join(risk.risk_factors) if risk.risk_factors else 'None'}

Provide your argument based strictly on your agent persona's goal.
Format your response EXACTLY as:
POSITION: [support, oppose, or compromise]
REASONING: [1-2 short sentences of your specific reasoning]
ALTERNATIVE: [if oppose/compromise, provide an alternative action. Otherwise leave empty]
CONFIDENCE: [0.0 to 1.0]"""
    
    try:
        messages = [SystemMessage(content=prompt)]
        response = llm.invoke(messages).content
        
        pos, reason, alt, conf = "support", f"{agent_name} supports this.", "", 0.8
        for line in response.split('\n'):
            line = line.strip()
            if line.startswith("POSITION:"): pos = line.split(":", 1)[1].strip().lower()
            elif line.startswith("REASONING:"): reason = line.split(":", 1)[1].strip()
            elif line.startswith("ALTERNATIVE:"): alt = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"): 
                try: conf = float(line.split(":", 1)[1].strip())
                except: pass
                
        return AgentArgument(agent_name=agent_name, position=pos, reasoning=reason, confidence=conf, alternative=alt)
    except Exception as e:
        print(f"[{agent_name}] LLM failed: {e}")
        return None


def _cost_agent_argue(opp: OptimizationOpportunity, sim: SimulationResult, risk: RiskAssessment, resource: dict) -> AgentArgument:
    """Cost Agent: Always pushes for maximum savings"""
    
    if sim.projected_savings > 500:
        position = "support"
        reasoning = f"High savings opportunity: ${sim.projected_savings:.0f}/month. ROI is clear. We should act immediately."
    elif sim.projected_savings > 200:
        position = "support"
        reasoning = f"Moderate savings of ${sim.projected_savings:.0f}/month. Cumulative impact across fleet is significant."
    else:
        position = "support"
        reasoning = f"Even ${sim.projected_savings:.0f}/month adds up. Small optimizations compound over time."
    
    confidence = min(sim.projected_savings / 1000, 0.95)
    
    return AgentArgument(
        agent_name="CostAgent",
        position=position,
        reasoning=reasoning,
        confidence=confidence
    )


def _risk_agent_argue(opp: OptimizationOpportunity, sim: SimulationResult, risk: RiskAssessment, resource: dict) -> AgentArgument:
    """Risk Agent: Focuses on safety and availability"""
    
    alternative = ""
    is_prod = resource.get("env") == "prod"
    is_database = resource.get("type") in ["rds", "database", "sql", "cloud_sql", "azure_sql"]
    is_destructive = opp.action in ["terminate", "delete"]
    
    if risk.risk_tier == "high":
        position = "oppose"
        reasoning = f"High risk: {', '.join(risk.risk_factors)}. "
        
        if is_prod and is_database:
            reasoning += "Production database changes require maintenance window and backup verification."
            alternative = f"Schedule {opp.action} during next maintenance window with rollback plan."
        elif is_destructive:
            reasoning += "Destructive action cannot be easily reversed."
            alternative = f"Consider 'stop' instead of '{opp.action}' to allow recovery if needed."
        else:
            reasoning += "Need thorough impact analysis before proceeding."
            alternative = "Conduct 24-hour monitoring period before action."
        
        confidence = 0.85
    elif risk.risk_tier == "medium":
        position = "compromise"
        reasoning = f"Moderate risk detected: {', '.join(risk.risk_factors[:2])}. "
        reasoning += "Action is viable with proper safeguards."
        alternative = f"Proceed with {opp.action} but implement automated rollback if metrics degrade."
        confidence = 0.65
    else:
        position = "support"
        reasoning = "Low risk profile. Standard change management procedures sufficient."
        confidence = 0.90
    
    return AgentArgument(
        agent_name="RiskAgent",
        position=position,
        reasoning=reasoning,
        confidence=confidence,
        alternative=alternative
    )


def _performance_agent_argue(opp: OptimizationOpportunity, sim: SimulationResult, risk: RiskAssessment, resource: dict) -> AgentArgument:
    """Performance Agent: Focuses on workload requirements"""
    
    alternative = ""
    current_cpu = resource.get("cpu_util", 0)
    projected_cpu = sim.projected_utilization
    
    if opp.action == "resize":
        if projected_cpu > 80:
            position = "oppose"
            reasoning = f"Projected CPU utilization of {projected_cpu:.0f}% is too high. "
            reasoning += "Leaves no headroom for traffic spikes or batch jobs."
            alternative = "Resize to intermediate instance type, not smallest option."
            confidence = 0.80
        elif projected_cpu > 60:
            position = "compromise"
            reasoning = f"Projected {projected_cpu:.0f}% CPU is acceptable but tight. "
            reasoning += "Monitor closely for 48 hours post-change."
            alternative = "Implement auto-scaling to handle bursts."
            confidence = 0.70
        else:
            position = "support"
            reasoning = f"Projected {projected_cpu:.0f}% CPU provides healthy headroom. Workload will run comfortably."
            confidence = 0.85
    
    elif opp.action == "schedule":
        position = "compromise"
        reasoning = "Scheduling reduces availability. Ensure no critical dependencies during off-hours."
        alternative = "Verify no overnight batch jobs, monitoring, or backup processes depend on this resource."
        confidence = 0.75
    
    elif opp.action in ["terminate", "delete"]:
        if current_cpu < 5:
            position = "support"
            reasoning = f"Resource is idle ({current_cpu:.1f}% CPU). No active workload detected."
            confidence = 0.90
        else:
            position = "oppose"
            reasoning = f"Resource shows {current_cpu:.1f}% utilization. May have intermittent or scheduled workloads."
            alternative = "Monitor for 7 days to confirm usage pattern before termination."
            confidence = 0.75
    else:
        position = "support"
        reasoning = "Action does not significantly impact performance characteristics."
        confidence = 0.70
    
    return AgentArgument(
        agent_name="PerformanceAgent",
        position=position,
        reasoning=reasoning,
        confidence=confidence,
        alternative=alternative if position != "support" else ""
    )


def _scheduler_agent_argue(opp: OptimizationOpportunity, sim: SimulationResult, risk: RiskAssessment, resource: dict) -> AgentArgument:
    """Scheduler Agent: Proposes timing-based compromises"""
    
    alternative = ""
    is_prod = resource.get("env") == "prod"
    is_dev = resource.get("env") == "dev"
    
    if opp.action in ["terminate", "delete"] and risk.risk_tier == "high":
        position = "compromise"
        reasoning = "High-risk destructive action. Timing can mitigate risk."
        
        if is_prod:
            alternative = "Execute during maintenance window (Saturday 2AM-6AM UTC) with on-call engineer standby."
        else:
            alternative = "Execute during business hours when team is available to respond if issues arise."
        
        confidence = 0.80
    
    elif opp.action == "resize" and is_prod:
        position = "compromise"
        reasoning = "Production resize should occur during low-traffic period."
        alternative = "Schedule resize for 3AM-5AM local time when traffic is typically 20% of peak."
        confidence = 0.75
    
    elif opp.action == "schedule":
        position = "support"
        reasoning = "Scheduling is inherently time-based. Recommend 9AM-6PM weekdays for dev resources."
        alternative = "For staging: 7AM-8PM weekdays. For dev: 9AM-6PM weekdays."
        confidence = 0.85
    
    elif is_dev and opp.action in ["terminate", "delete"]:
        position = "support"
        reasoning = "Dev resource can be safely modified during business hours. Team available to recreate if needed."
        alternative = "Execute between 10AM-4PM when developers are online."
        confidence = 0.90
    
    else:
        position = "support"
        reasoning = "Standard timing applies. No special scheduling constraints."
        confidence = 0.70
    
    return AgentArgument(
        agent_name="SchedulerAgent",
        position=position,
        reasoning=reasoning,
        confidence=confidence,
        alternative=alternative
    )


def _consensus_agent_decide(arguments: List[AgentArgument], opp: OptimizationOpportunity, resource: dict) -> Dict[str, Any]:
    """Consensus Agent: Synthesizes all arguments and makes final decision"""
    
    # Count positions
    support_count = sum(1 for arg in arguments if arg.position == "support")
    oppose_count = sum(1 for arg in arguments if arg.position == "oppose")
    compromise_count = sum(1 for arg in arguments if arg.position == "compromise")
    
    # Weighted confidence
    total_confidence = sum(arg.confidence for arg in arguments) / len(arguments)
    
    # Collect alternatives
    alternatives = [arg.alternative for arg in arguments if arg.alternative]
    
    # Decision logic
    if oppose_count >= 2:
        # Strong opposition
        decision = "rejected"
        consensus_action = "no_action"
        reasoning = f"Rejected: {oppose_count} agents oppose. "
        reasoning += "Primary concerns: " + "; ".join([arg.reasoning for arg in arguments if arg.position == "oppose"])
        
        if alternatives:
            reasoning += f" Suggested alternatives: {alternatives[0]}"
        
        confidence = 1.0 - total_confidence
    
    elif support_count >= 3:
        # Strong support
        decision = "approved"
        consensus_action = opp.action
        reasoning = f"Approved: {support_count} agents support. "
        reasoning += "Consensus: " + "; ".join([arg.reasoning for arg in arguments if arg.position == "support"][:2])
        confidence = total_confidence
    
    elif compromise_count >= 2 or (support_count >= 1 and compromise_count >= 1):
        # Compromise needed
        decision = "modified"
        
        # Select best alternative
        if alternatives:
            consensus_action = alternatives[0]
            reasoning = f"Modified approach: {compromise_count} agents suggest compromise. "
            reasoning += f"Consensus: {alternatives[0]}"
        else:
            consensus_action = f"{opp.action}_with_monitoring"
            reasoning = f"Approved with conditions: Proceed with {opp.action} but implement enhanced monitoring and rollback plan."
        
        confidence = total_confidence * 0.85
    
    else:
        # Mixed signals, default to caution
        decision = "rejected"
        consensus_action = "defer_for_review"
        reasoning = "No clear consensus. Defer to human review."
        confidence = 0.50
    
    return {
        "decision": decision,
        "consensus_action": consensus_action,
        "reasoning": reasoning,
        "confidence": confidence
    }


def _use_llm_for_consensus(arguments: List[AgentArgument], opp: OptimizationOpportunity, resource: dict) -> Dict[str, Any]:
    """Use LLM to synthesize arguments and make decision"""
    llm = _get_llm()
    if not llm:
        return _consensus_agent_decide(arguments, opp, resource)
    
    try:
        # Format arguments for LLM
        debate_text = f"Resource: {opp.resource_id} ({resource.get('type')}, {resource.get('env')})\n"
        debate_text += f"Proposed Action: {opp.action}\n"
        debate_text += f"Estimated Savings: ${opp.estimated_savings:.0f}/month\n\n"
        debate_text += "Agent Arguments:\n"
        
        for arg in arguments:
            debate_text += f"\n[{arg.agent_name}] Position: {arg.position.upper()}\n"
            debate_text += f"  Reasoning: {arg.reasoning}\n"
            if arg.alternative:
                debate_text += f"  Alternative: {arg.alternative}\n"
            debate_text += f"  Confidence: {arg.confidence:.0%}\n"
        
        system_prompt = """You are a ConsensusAgent that synthesizes multiple agent arguments to make final decisions.
Analyze the debate and provide:
1. Final decision: approved, rejected, or modified
2. Consensus action: what action to take
3. Brief reasoning (2-3 sentences)
4. Confidence score (0.0-1.0)

Format your response as:
DECISION: [approved/rejected/modified]
ACTION: [action to take]
REASONING: [your reasoning]
CONFIDENCE: [0.0-1.0]"""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=debate_text)
        ]
        
        response = llm.invoke(messages)
        content = response.content
        
        # Parse LLM response
        lines = content.strip().split("\n")
        result = {}
        for line in lines:
            if line.startswith("DECISION:"):
                result["decision"] = line.split(":", 1)[1].strip().lower()
            elif line.startswith("ACTION:"):
                result["consensus_action"] = line.split(":", 1)[1].strip()
            elif line.startswith("REASONING:"):
                result["reasoning"] = line.split(":", 1)[1].strip()
            elif line.startswith("CONFIDENCE:"):
                try:
                    result["confidence"] = float(line.split(":", 1)[1].strip())
                except:
                    result["confidence"] = 0.75
        
        # Validate and fill defaults
        if "decision" not in result:
            result["decision"] = "rejected"
        if "consensus_action" not in result:
            result["consensus_action"] = "no_action"
        if "reasoning" not in result:
            result["reasoning"] = "LLM consensus analysis"
        if "confidence" not in result:
            result["confidence"] = 0.75
        
        return result
    
    except Exception as e:
        print(f"[ConsensusAgent] LLM failed: {e}, falling back to rule-based")
        return _consensus_agent_decide(arguments, opp, resource)


def run_debate(opp: OptimizationOpportunity, sim: SimulationResult, risk: RiskAssessment, use_llm: bool = True) -> DebateResult:
    """
    Run multi-agent debate for a single optimization opportunity
    
    Args:
        opp: Optimization opportunity
        sim: Simulation result
        risk: Risk assessment
        use_llm: Whether to use LLM for consensus (requires GROQ_API_KEY)
    
    Returns:
        DebateResult with full debate transcript and consensus decision
    """
    resource = get_resource(opp.resource_id)
    
    # Round 1: Initial arguments
    if use_llm and GROQ_AVAILABLE:
        round1 = [
            _llm_argue("CostAgent", "Maximize cost savings aggressively", opp, sim, risk, resource) or _cost_agent_argue(opp, sim, risk, resource),
            _llm_argue("RiskAgent", "Minimize operational risk and ensure safety", opp, sim, risk, resource) or _risk_agent_argue(opp, sim, risk, resource),
            _llm_argue("PerformanceAgent", "Ensure sufficient workload performance headroom", opp, sim, risk, resource) or _performance_agent_argue(opp, sim, risk, resource),
            _llm_argue("SchedulerAgent", "Propose optimal timing and maintenance windows", opp, sim, risk, resource) or _scheduler_agent_argue(opp, sim, risk, resource),
        ]
    else:
        round1 = [
            _cost_agent_argue(opp, sim, risk, resource),
            _risk_agent_argue(opp, sim, risk, resource),
            _performance_agent_argue(opp, sim, risk, resource),
            _scheduler_agent_argue(opp, sim, risk, resource),
        ]
    
    # Consensus decision
    if use_llm and GROQ_AVAILABLE:
        consensus = _use_llm_for_consensus(round1, opp, resource)
    else:
        consensus = _consensus_agent_decide(round1, opp, resource)
    
    # Generate debate summary
    summary = f"Debate for {opp.resource_id} ({opp.action}):\n"
    for arg in round1:
        emoji = "✅" if arg.position == "support" else "❌" if arg.position == "oppose" else "⚖️"
        summary += f"{emoji} [{arg.agent_name}] {arg.reasoning[:80]}...\n"
    summary += f"\n🤝 [ConsensusAgent] {consensus['reasoning']}"
    
    return DebateResult(
        resource_id=opp.resource_id,
        original_action=opp.action,
        debate_rounds=[round1],
        final_decision=consensus["decision"],
        consensus_action=consensus["consensus_action"],
        consensus_reasoning=consensus["reasoning"],
        confidence=consensus["confidence"],
        debate_summary=summary
    )


def run_debate_batch(opportunities: List[OptimizationOpportunity], 
                     simulations: List[SimulationResult],
                     risks: List[RiskAssessment],
                     use_llm: bool = True) -> List[DebateResult]:
    """Run debates for multiple opportunities"""
    results = []
    for opp, sim, risk in zip(opportunities, simulations, risks):
        result = run_debate(opp, sim, risk, use_llm=use_llm)
        results.append(result)
    return results
