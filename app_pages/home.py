from pathlib import Path

import streamlit as st

from components import render_real_world_examples, render_references
from content import links as L
from content import story
import dry_run

_STATIC = Path(__file__).parent.parent / "static"

st.image(str(_STATIC / "snowflake_full_logo.png"), width=180)
st.title("Borrowell's Product Insights Agent")
dry_run.banner()
st.markdown("From raw offer telemetry to a governed agent that reads out experiments - and that Workwell can call - "
            "using only prompts in **CoCo**.")
st.space("small")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Core lab", "75 min", help="Sessions 1-5")
c2.metric("Prompts", "12 core", help="Plus 3 stretch prompts")
c3.metric("You build", "6 objects", help="Views, semantic view, search service, agent, MCP server, ranking function")
c4.metric("Eval", "6 questions", help="Checked against governed numbers")

st.space("medium")
st.markdown("#### :material/groups: Who's in this story")
story.cast()
st.markdown("#### :material/report: The problem")
with st.chat_message("Priya", avatar=":material/campaign:"):
    st.markdown("**Priya, Marketplace Growth:** *\"EXP-114 ranked offers by payout instead of relevance. CTR went up. "
                "Can we ship it?\"*")
st.markdown("Borrowell earns referral revenue when a partner **approves** an application - not when a member clicks. "
            "Workwell, Borrowell's internal AI assistant, can't answer this yet: it isn't connected to Snowflake because "
            "answers from raw tables were inaccurate and there's no semantic layer. So the question becomes a Looker ticket:")
story.timelines()

st.markdown("#### :material/route: What, how and why")
w, h, y = st.columns(3)
with w.container(border=True, height="stretch"):
    st.markdown("##### :material/flag: What")
    st.markdown("""
In 90 minutes you:
1. find three data traps in the telemetry,
2. give CTR, approvals and revenue one definition,
3. index the team's experiment knowledge,
4. build an agent that reads out EXP-114,
5. catch it being wrong, fix it, and hand it to Workwell,
6. *(stretch)* rank offers by expected revenue.
""")
with h.container(border=True, height="stretch"):
    st.markdown("##### :material/terminal: How")
    st.markdown("""
- **Prompts only**, in **CoCo Desktop or CoCo CLI**. CoCo shows the SQL before it runs anything.
- Every step also shows **how to do it in Snowsight**, and a *Behind? Run this* box with the tested SQL.
- Synthetic telemetry in a shared, read-only `DATA` schema; you build in **your own schema** `LAB_<NAME>`.
""")
with y.container(border=True, height="stretch"):
    st.markdown("##### :material/lightbulb: Why this approach")
    st.markdown("""
- It's a **real product data science question** with a real trap: a leading metric that wins while the business loses.
- It mirrors the plan for **Workwell**: a governed Snowflake sub-agent per domain, exposed over **MCP**.
- The **eval** is the habit that makes agents safe to put in front of the business.
""")

st.markdown("#### :material/account_tree: What you build")
st.graphviz_chart("""
digraph {
  rankdir=LR; node [shape=box, style="rounded,filled", fillcolor="#F0F4F8", color="#29B5E8", fontname="Helvetica"];
  raw [label="DATA (shared)\\nTELEMETRY_EVENTS, APPLICATIONS\\nMEMBERS, PARTNER_OFFERS"];
  views [label="Curated views\\nno bots, no test accounts,\\nno duplicate events"];
  sv [label="PRODUCT_INSIGHTS_SV\\n(semantic view)"];
  docs [label="EXPERIMENT_DOCS"]; css [label="EXPERIMENT_DOCS_SEARCH\\n(Cortex Search)"];
  fn [label="RECOMMEND_OFFERS\\n(stretch)", fillcolor="#FFF4E0"];
  agent [label="PRODUCT_INSIGHTS_AGENT\\n(Cortex Agent)", fillcolor="#E3F5FC"];
  ev [label="agent_eval.py\\n6 checks", fillcolor="#E3F5FC"];
  mcp [label="PRODUCT_INSIGHTS_MCP\\n(managed MCP server)"]; ww [label="Workwell", fillcolor="#E8F5E9"];
  raw -> views -> sv -> agent; docs -> css -> agent; fn -> agent; agent -> mcp -> ww;
  ev -> agent [style=dashed, arrowhead=none];
}
""")

st.markdown("#### :material/checklist: What this lab answers")
st.caption("Themes from Borrowell's calls with the Snowflake team (Sep-Nov 2026).")
st.markdown("""
| Borrowell need | Covered in |
|---|---|
| Workwell answers were inaccurate without a semantic layer | Sessions 2 and 5 |
| Explore Snowflake data directly instead of going through Looker | Sessions 1, 2 and 4 |
| A product data science agent on telemetry (clicks, impressions) | Sessions 1-5 |
| Hands-on time with CoCo, including the GenAI Ops team | Every prompt |
| Workwell as the front door, Snowflake agents as sub-agents (MCP) | Session 5 |
| Prove GenAI value with a business outcome | Stretch |
""")
st.caption("All partners, offers, members and numbers are synthetic. No Borrowell data is used.")

render_real_world_examples([
    {"title": "Experiment readouts in minutes", "body": "Every experiment with a brief in the knowledge base gets the same readout - primary metric, guardrails, revenue - without a Looker ticket."},
    {"title": "Workwell meets Snowflake", "body": "The MCP server is the missing connector: Workwell asks, the Snowflake agent answers with governed numbers under the caller's role."},
    {"title": "Release and data-issue awareness", "body": "Known issues (like a double-firing app version) are searched before a metric change is called real."},
    {"title": "Ranking for approvals", "body": "The stretch turns the readout into a better carousel: ranked by what members are likely to be approved for."},
])
render_references({
    "Quickstarts": [L.QS_SV, L.QS_AGENTS, L.QS_COCO_DESKTOP],
    "Docs": [L.SV_OVERVIEW, L.SEARCH, L.AGENTS, L.MCP, L.COCO],
})
