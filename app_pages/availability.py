import streamlit as st

from components import render_real_world_examples, render_references
from content import links as L

st.title("Azure Canada Central availability")
st.markdown("Borrowell's Snowflake account is on **Azure Canada Central**. Feature and model availability can differ by cloud and region.")
st.warning(
    "This lab was dry-run on a Snowflake demo account in AWS Canada Central, not in Borrowell's account. "
    "The admin should confirm each item below in Borrowell's account with the pre-flight checks in `00_admin_setup.sql`.",
    title="Verify before the session",
)

st.markdown("#### :material/checklist: Features this lab uses")
st.markdown("""
| Feature | Used in | How to confirm in your account |
|---|---|---|
| Semantic views (`SYSTEM$CREATE_SEMANTIC_VIEW_FROM_YAML`) | Session 2 | Create succeeds in an attendee schema |
| Cortex Analyst | Sessions 2, 4 | Analyst playground answers on the semantic view |
| Cortex Search | Session 3 | `CREATE CORTEX SEARCH SERVICE` succeeds; `SEARCH_PREVIEW` returns results |
| Cortex Agents + `DATA_AGENT_RUN` | Sessions 4-5 | `CREATE AGENT` succeeds and `DATA_AGENT_RUN` returns an answer |
| Orchestration model `claude-sonnet-4-5` | Sessions 4-5 | `SHOW CORTEX BASE MODELS;` - needs cross-region inference here; or use `auto` |
| Custom agent tools (scalar UDF) | Stretch | Agent trace shows `recommend_offers` returning rows |
| Snowflake-managed MCP servers | Session 5 | `CREATE MCP SERVER` succeeds |
| CoCo Desktop / CLI | All | Sign-in to the account |
""")

st.markdown("#### :material/shield: Cross-region inference")
st.markdown("""
`CORTEX_ENABLED_CROSS_REGION` decides whether Cortex may process a request outside Azure Canada Central when a model isn't
available locally. Check it with `SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;` and agree the setting with
Borrowell's security team (they completed a Cortex/CoCo security review in August). The lab data is synthetic.
""")

render_real_world_examples([
    {"title": "Pre-flight before the workshop", "body": "The admin runs the checks above the day before and records any gaps on this page."},
    {"title": "Model choice for production agents", "body": "Pick the orchestration model per agent based on what's available in-region and the residency policy."},
])
render_references({"Docs": [L.CROSS_REGION, L.AGENTS, L.SEARCH, L.MCP]})
