import streamlit as st

from components import ctx, fill, render_real_world_examples, render_references
from content import links as L

st.title("Getting started")
st.markdown("Five minutes before the lab starts. Your admin has already created your workspace - you only connect and check.")

st.markdown("#### :material/laptop: Bring")
with st.container(border=True):
    st.markdown("""
| Item | Details |
|---|---|
| **CoCo Desktop or CoCo CLI** | Signed in to Borrowell's Snowflake account. Either works for every step. |
| **Your lab name** | From Archana, usually your first name (e.g. `ARCHANA`). Type it in the sidebar - every prompt updates. |
| **Browser** | Snowsight, for the *Do it in Snowsight* routes and the agent Playground. |
| **Session 5 (optional)** | Snowflake CLI (`snow`) and Python 3.10+ (or `uv`) to run the eval yourself. |
""")

c = ctx()
st.markdown("#### :material/checklist: Check your setup")
st.markdown("##### 1. Connect CoCo and switch to your lab role")
with st.container(border=True):
    st.warning("**You have to set your role yourself.** The lab grants you role "
               f"`{c['ROLE']}` but doesn't make it your default, so CoCo and Snowsight start in your usual role. "
               "Switch now, and again after any reconnect, new CoCo session or new worksheet.",
               icon=":material/badge:")
    st.markdown(fill("""
- **CoCo Desktop**: choose your Borrowell connection, then set role **`{ROLE}`** and warehouse **`{WH}`**.
- **CoCo CLI**: start `cortex` (or `cortex -c <your-connection>`), then ask: *"use role {ROLE}, secondary roles none and warehouse {WH}"*.
"""))

st.markdown("##### 2. Paste this into CoCo")
with st.container(border=True):
    st.code(fill("Confirm my current role, warehouse and that I can see schema {FQ_SCHEMA}. Then list the tables in "
                 "BORROWELL_AGENT_LAB.DATA with their row counts."), language="text", wrap_lines=True)
    st.markdown(fill("""
You should see:
- role **`{ROLE}`**, warehouse **`{WH}`**
- your schema `{FQ_SCHEMA}` - **empty** (you build everything in it)
- 8 tables in `DATA`: `APPLICATIONS`, `EXPERIMENTS`, `EXPERIMENT_ASSIGNMENTS`, `EXPERIMENT_DOCS`, `MEMBERS`, `OFFER_RANKINGS`, `PARTNER_OFFERS`, `TELEMETRY_EVENTS`
"""))
    with st.expander(":material/web: Do it in Snowsight"):
        st.code(fill(f"""USE ROLE {c['ROLE']};
USE SECONDARY ROLES NONE;
USE WAREHOUSE {c['WH']};
SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE();
SHOW OBJECTS IN SCHEMA {c['FQ_SCHEMA']};
SHOW TABLES IN SCHEMA BORROWELL_AGENT_LAB.DATA;"""), language="sql")

st.markdown("##### 3. Know the isolation model")
with st.container(border=True):
    st.markdown(fill("""
- One lab database: `BORROWELL_AGENT_LAB`. **Your schema `{SCHEMA}` is yours** - you own everything you create in it.
- Shared and read-only: `DATA` (synthetic telemetry, members, offers, applications, experiment docs).
- You can't see anyone else's schema, agent or MCP server.
- One shared warehouse `{WH}`, capped by a resource monitor.
"""))

st.markdown("##### 4. How to work in CoCo")
with st.container(border=True):
    st.markdown("""
- Paste the prompt as is. CoCo shows the SQL before it runs anything - **read it, then approve**.
- If CoCo asks a question, answer with the details in the prompt.
- Ticking **Done** on a prompt marks the page complete in the sidebar.
- Behind? Every section has a **Behind? Run this** box with the exact, tested SQL.
""")

render_real_world_examples([
    {"title": "Same pattern in production", "body": "A data scientist connects CoCo with a role scoped to the product data, and explores without a Looker ticket."},
    {"title": "CLI for repeatable runs", "body": "The CoCo CLI can be scripted, so the same eval and prompts can run in CI."},
])
render_references({"Quickstarts": [L.QS_COCO_DESKTOP, L.QS_COCO_CLI, L.QS_COCO_BP], "Docs": [L.COCO, L.COCO_CLI]})
