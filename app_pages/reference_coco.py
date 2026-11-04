import streamlit as st

from components import fill, render_real_world_examples, render_references
from content import links as L

st.title("CoCo prompt cheat sheet")
st.markdown("Prompts that worked well in the lab, ready to reuse on Borrowell's own product data.")

st.markdown("#### :material/tips_and_updates: How to prompt CoCo for agent work")
st.markdown("""
- **Name objects fully** (`DATABASE.SCHEMA.OBJECT`) and the role to use.
- **State the definition** ("count DISTINCT client_event_id", "exclude is_test") - CoCo turns it into a governed metric.
- **Ask to see the SQL or spec first** for anything that creates or changes objects.
- **Ask for the trace**: which tools the agent called and what SQL it ran - not only the answer.
- **Use the skills**: `/semantic_studio` for semantic views; CoCo also loads its agent and search skills on its own.
""")

prompts = {
    "Profile a new event stream": "Profile {FQ_SCHEMA}.<EVENTS_TABLE>: event types, raw vs distinct event ids, bot and internal traffic, and daily volume by platform and app version. What looks suspicious?",
    "Add a metric to the semantic view": "Add a metric revenue_per_click (referral_revenue / clicks) to {FQ_SCHEMA}.PRODUCT_INSIGHTS_SV, without joining events to applications in one query. Show the YAML change first.",
    "Add a verified query": "Add a verified query 'EXP-114 readout by arm' to {FQ_SCHEMA}.PRODUCT_INSIGHTS_SV using the exp114 metrics, then re-run tools/agent_eval.py.",
    "Read out any experiment": "Ask {FQ_SCHEMA}.PRODUCT_INSIGHTS_AGENT: read out <EXPERIMENT_ID> against its brief - primary metric, guardrails and revenue per exposed member.",
    "Segment check": "Using {FQ_SCHEMA}.PRODUCT_INSIGHTS_SV, is EXP-114's approval-rate drop the same for newcomers to Canada and for each province?",
    "Watch for double-fires": "Create a data metric function that flags a day when raw offer_impression rows exceed distinct client_event_id by more than 2%, and attach it to BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS.",
}
for title, p in prompts.items():
    with st.container(border=True):
        st.markdown(f"**{title}**")
        st.code(fill(p), language="text", wrap_lines=True)

render_real_world_examples([
    {"title": "Team playbook", "body": "Save these prompts as a CoCo skill so every analyst builds and checks agents the same way."},
    {"title": "Scripted evals", "body": "Run the eval with the CoCo CLI or in CI every time the semantic view changes."},
])
render_references({"Quickstarts": [L.QS_COCO_BP, L.QS_COCO_DE, L.QS_SV_BP], "Docs": [L.COCO, L.COCO_CLI]})
