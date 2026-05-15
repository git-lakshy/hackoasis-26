import streamlit as st
import plotly.express as px
import pandas as pd
import json
from pathlib import Path
from data.mock_cloud import get_resources_live as get_resources, reset_state
import os
from agents.supervisor import run_cycle, resume_with_approval, chat
from memory.store import seed_memory

st.set_page_config(title='FinOps AI Agent', layout='wide', page_icon='💰')

for k, v in {'graph_state': {}, 'approval_queue': [], 'trace': [], 'messages': [], 'cycle_run': False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Sidebar
with st.sidebar:
    st.title('💰 FinOps AI Agent')

    demo_mode = st.checkbox('Demo Mode')
    if demo_mode and not st.session_state.get('_seeded'):
        seed_memory()
        st.session_state['_seeded'] = True

    if st.button('▶ Run Optimization Cycle'):
        state = run_cycle()
        st.session_state.graph_state = state
        st.session_state.approval_queue = state.get('approval_queue', [])
        st.session_state.trace = state.get('trace', [])
        st.session_state.cycle_run = True

    if st.button('🔄 Reset Demo'):
        reset_state()
        for k in ['graph_state', 'approval_queue', 'trace', 'messages', 'cycle_run', '_seeded']:
            st.session_state.pop(k, None)
        st.rerun()

    if st.session_state.cycle_run:
        state = st.session_state.graph_state
        resources = get_resources()
        findings = state.get('findings', [])
        auto_savings = sum(sim.projected_savings for opp, sim, risk in state.get('auto_queue', []))
        appr_savings = sum(sim.projected_savings for opp, sim, risk in state.get('approval_queue', []))
        st.metric('Total Resources', len(resources))
        st.metric('Findings', len(findings))
        st.metric('Potential Savings', f"${auto_savings + appr_savings:,.0f}/mo")

# Main tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(['Cost Overview', 'Agent Trace', 'Action Log', 'Approval Queue', 'Chat'])

with tab1:
    resources = get_resources()
    df = pd.DataFrame(resources)
    if not df.empty and 'cloud' in df.columns and 'monthly_cost' in df.columns:
        spend_df = df.groupby('cloud', as_index=False)['monthly_cost'].sum()
        st.plotly_chart(px.bar(spend_df, x='cloud', y='monthly_cost', title='Monthly Spend by Cloud'), use_container_width=True)

        total_spend = df['monthly_cost'].sum()
        state = st.session_state.graph_state
        auto_savings = sum(sim.projected_savings for opp, sim, risk in state.get('auto_queue', []))
        appr_savings = sum(sim.projected_savings for opp, sim, risk in state.get('approval_queue', []))
        exec_savings = sum(r.actual_savings or 0 for r in state.get('executed', []))

        c1, c2, c3 = st.columns(3)
        c1.metric('Total Spend', f"${total_spend:,.0f}/mo")
        c2.metric('Identified Savings', f"${auto_savings + appr_savings:,.0f}/mo")
        c3.metric('Executed Savings', f"${exec_savings:,.0f}/mo")

        if st.session_state.cycle_run:
            st.subheader('Before / After')
            b, a = st.columns(2)
            b.metric('Before', f"${total_spend:,.0f}/mo")
            a.metric('After', f"${total_spend - exec_savings:,.0f}/mo", delta=f"-${exec_savings:,.0f}")

with tab2:
    if st.session_state.trace:
        for msg in st.session_state.trace:
            st.info(msg)
    else:
        st.info('Run a cycle to see agent reasoning')

with tab3:
    log_path = Path('data/action_log.json')
    log = json.loads(log_path.read_text()) if log_path.exists() else []
    if log:
        log_df = pd.DataFrame(log)[['action_id', 'resource_id', 'action', 'risk_tier', 'simulated_savings', 'actual_savings', 'accuracy']]
        tier_colors = {'low': 'green', 'medium': 'orange', 'high': 'red'}
        st.dataframe(
            log_df,
            column_config={
                'risk_tier': st.column_config.TextColumn('Risk Tier'),
                'simulated_savings': st.column_config.NumberColumn('Sim. Savings', format='$%.2f'),
                'actual_savings': st.column_config.NumberColumn('Actual Savings', format='$%.2f'),
                'accuracy': st.column_config.NumberColumn('Accuracy', format='%.2f'),
            },
            use_container_width=True,
        )
    else:
        st.info('No actions executed yet')

with tab4:
    queue = st.session_state.approval_queue
    if queue:
        for i, (opp, sim, risk) in enumerate(queue):
            with st.container(border=True):
                st.write(f"**{opp.resource_id}** — {opp.action}")
                st.write(f"Risk: `{risk.risk_tier}` | Factors: {', '.join(risk.risk_factors)}")
                st.write(f"Projected Savings: **${sim.projected_savings:,.0f}/mo** | Confidence: {sim.confidence:.0%}")
                col1, col2 = st.columns(2)
                if col1.button('✅ Approve', key=f'approve_{i}'):
                    new_state = resume_with_approval(st.session_state.graph_state, [opp.resource_id])
                    st.session_state.graph_state = new_state
                    st.session_state.trace = new_state.get('trace', [])
                    st.session_state.approval_queue = [item for j, item in enumerate(queue) if j != i]
                    st.rerun()
                if col2.button('❌ Reject', key=f'reject_{i}'):
                    st.session_state.approval_queue = [item for j, item in enumerate(queue) if j != i]
                    st.rerun()
    else:
        st.success('No pending approvals')

with tab5:
    for msg in st.session_state.messages:
        with st.chat_message(msg['role']):
            st.write(msg['content'])

    if prompt := st.chat_input('Ask about your infrastructure costs...'):
        st.session_state.messages.append({'role': 'user', 'content': prompt})
        response = chat(prompt, st.session_state.graph_state)
        st.session_state.messages.append({'role': 'assistant', 'content': response})
        with st.chat_message('assistant'):
            st.write(response)
