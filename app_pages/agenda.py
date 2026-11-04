import streamlit as st

from components import render_real_world_examples, render_references
from content import links as L
from content import story

st.title("Agenda")
story.story_arc(0)
st.markdown("Tuesday 10 November, **2:30-4:00 PM**, York St, Toronto and Zoom. One workspace each.")

st.markdown("""
| Time | Section | You do (in CoCo) | Snowflake capability |
|---|---|---|---|
| 0-10 | **1. Explore the telemetry** | Profile the funnel; find why CTR "dropped" | CoCo data discovery |
| 10-30 | **2. Build the semantic layer** | Curated views + governed metrics | Semantic views, Cortex Analyst |
| 30-40 | **3. Add knowledge with Search** | Index briefs, definitions, data issues | Cortex Search |
| 40-60 | **4. Build the agent** | Create it; ask Priya's and Marco's questions | Cortex Agents, DATA_AGENT_RUN |
| 60-75 | **5. Evaluate and connect Workwell** | Eval, find the wrong answer, fix it, MCP | Evals, managed MCP server |
| 75-90 | **Stretch: approval-aware ranking** | Expected-revenue ranking + projected lift | Custom agent tools |
""")

with st.container(border=True):
    st.markdown("""
**Before the lab (1:00-2:30):** why AI on Snowflake, AI Gateway, CoCo demo (data discovery, Horizon Context, guardrails).

**After the session:** the guide stays online and your schema is kept until the admin runs teardown. The stretch works as a take-home.
""")

st.markdown("#### :material/bug_report: The traps in the data")
st.caption("Realistic issues seeded in the shared telemetry. Finding them is part of the lab.")
st.markdown("""
| Trap | What happened | Symptom |
|---|---|---|
| Bot traffic | Scripted, logged-out sessions click most offers | CTR about 2 points too high |
| Test accounts | QA and employee accounts click and apply constantly | Inflated clicks and applications |
| Android 5.2.0 | Dashboard impressions sent twice from 21 Sep | CTR appears to fall 12% |
| Fan-out | Events joined to applications in one query | Revenue about 7x too high in the readout |
| Leading-metric win | Payout ranking lifts CTR, cuts approvals | A dashboard says ship; the business says don't |
""")

render_real_world_examples([
    {"title": "The failure modes of product analytics", "body": "Bots, internal traffic, client double-fires and fan-out joins are the usual suspects behind a wrong metric. Each maps to one fix in the semantic layer."},
    {"title": "Guardrail metrics", "body": "A primary metric plus guardrails is how Borrowell can keep experiments honest - and the agent reads both."},
])
render_references({"Quickstarts": [L.QS_SV, L.QS_AGENTS], "Docs": [L.SV_OVERVIEW, L.AGENTS]})
