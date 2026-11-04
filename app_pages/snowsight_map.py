import streamlit as st

from components import render_real_world_examples, render_references
from content import links as L

st.title("Snowsight navigation map")
st.markdown("Where each lab step lives in Snowsight. Menu names can change between releases; if a label differs, use the Snowsight search bar.")

st.markdown("""
| Task | Snowsight location |
|---|---|
| Browse the shared telemetry and your schema | **Catalog » Database Explorer** » `BORROWELL_AGENT_LAB` » `DATA` / `LAB_<NAME>` |
| Create and test semantic views | **AI & ML » Cortex Analyst** |
| Create and test Cortex Search services | **AI & ML » Cortex Search** |
| Create agents, chat in the Playground, read the trace | **AI & ML » Agents** |
| Run SQL | **Projects » Workspaces** (or a worksheet) |
| MCP servers | Worksheet: `SHOW MCP SERVERS IN SCHEMA BORROWELL_AGENT_LAB.LAB_<NAME>;` |
| Query history (see the SQL the agent ran) | **Monitoring » Query history** |
| Cortex and warehouse cost | **Admin » Cost management** |
""")

render_real_world_examples([
    {"title": "Business users without CoCo", "body": "Product and marketing can use the agent in the Playground or Snowflake Intelligence, with no prompts to paste."},
    {"title": "Debugging an answer", "body": "Query history shows every statement the agent ran, under the caller's role."},
])
render_references({"Docs": [L.SV_OVERVIEW, L.SEARCH, L.AGENTS]})
