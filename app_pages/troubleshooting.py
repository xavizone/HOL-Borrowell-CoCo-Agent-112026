import streamlit as st

from components import fill, render_real_world_examples, render_references
from content import links as L

st.title("Troubleshooting")
st.markdown("Problems seen in the dry run and how to fix them.")

issues = [
    ("'Object does not exist or not authorized' on DATA or your schema",
     "CoCo is on your usual role. Switch, and turn secondary roles off so you see what your lab role sees:",
     "USE ROLE {ROLE};\nUSE SECONDARY ROLES NONE;\nUSE WAREHOUSE {WH};\nSELECT CURRENT_ROLE(), CURRENT_SECONDARY_ROLES();"),
    ("Semantic view YAML error",
     "Paste the error back to CoCo and ask it to fix it. Common causes: a relationship column that isn't declared as a "
     "fact or dimension, or a missing primary key on the right-hand (one) table.", None),
    ("`Insufficient privileges ... CHANGE_TRACKING` creating the search service",
     "The source table needs change tracking. The admin runs:",
     "ALTER TABLE BORROWELL_AGENT_LAB.DATA.EXPERIMENT_DOCS SET CHANGE_TRACKING = TRUE;"),
    ("Agent: model not available / no answer",
     "Cross-region inference is off or the model isn't allowed. List what you can use and switch the orchestration model "
     "(or use `auto`):", "SHOW CORTEX BASE MODELS;"),
    ("`TOOL_NOT_ACCESSIBLE` warning in the agent response",
     "The agent can't reach the semantic view or search service, or the name in `tool_resources` is wrong. Check:",
     "SHOW SEMANTIC VIEWS IN SCHEMA {FQ_SCHEMA};\nSHOW CORTEX SEARCH SERVICES IN SCHEMA {FQ_SCHEMA};"),
    ("Agent revenue in the millions", "That's the fan-out Session 5 fixes - do Prompt 5.2.", None),
    ("Custom tool: 'Unknown user-defined function'",
     "Agent custom tools call **scalar** functions. Point the tool at `RECOMMEND_OFFERS_TOOL` (returns an ARRAY), not the "
     "table function `RECOMMEND_OFFERS`.", None),
    ("`agent_eval.py` can't connect",
     "Pass `--connection <name>` from `snow connection list`, and check your lab role is granted to your user:",
     "SHOW GRANTS TO ROLE {ROLE};"),
    ("Everything is broken - start again",
     "Ask the facilitator to reset your workspace (empties your schema in seconds), then run each session's *Behind?* box.", None),
]
for title, body, sql in issues:
    with st.expander(f":material/help: {title}"):
        st.markdown(body)
        if sql:
            st.code(fill(sql), language="sql")

render_real_world_examples([
    {"title": "Rollout runbook", "body": "These fixes become the runbook when more domain agents go behind Workwell."},
    {"title": "Least-privilege checks", "body": "Authorisation errors prove each agent only sees what its caller's role can see - keep them."},
])
render_references({"Docs": [L.AGENTS_MANAGE, L.SEARCH_CREATE, L.SV_CREATE, L.CROSS_REGION]})
