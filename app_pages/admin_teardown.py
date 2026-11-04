import streamlit as st

from components import render_real_world_examples, render_references, render_sql_file
from content import links as L

st.title("Lab teardown (admin)")
st.markdown("Remove everything the lab created, in one script. Safe to re-run - every statement is `IF EXISTS`.")

st.markdown("#### :material/format_list_numbered: What 98_teardown.sql does, in order")
st.markdown("""
1. Drops every attendee role listed in `ADMIN.ROSTER` (`PI_LAB_<NAME>`, spares included).
2. `DROP DATABASE BORROWELL_AGENT_LAB` - shared data, every `LAB_*` schema, semantic views, search services, agents, MCP servers.
3. Drops `PI_LAB_WH` and `PI_LAB_MONITOR`.
4. Drops `PI_LAB_ATTENDEE` and `PI_LAB_ADMIN`.
""")
st.info("Run it as ACCOUNTADMIN from a warehouse other than `PI_LAB_WH`. Agree a date with attendees first - their agents go with it.",
        icon=":material/info:")
render_sql_file("98_teardown.sql", ":material/description: 98_teardown.sql", expanded=True)

st.markdown("#### :material/rule: After teardown")
st.markdown("""
- No user's default role or warehouse was changed by setup, so there's nothing to restore.
- If Workwell was pointed at a lab MCP server, remove that connection.
- Dropped data stays in Time Travel and then Fail-safe for the retention period. All lab data is synthetic.
""")

render_real_world_examples([
    {"title": "Clean sandboxes", "body": "One teardown script keeps the account free of stray roles, warehouses, agents and cost."},
    {"title": "Repeatable", "body": "Setup and teardown together rebuild the lab in minutes for the next cohort."},
])
render_references({"Docs": [L.TIME_TRAVEL, L.RES_MON]})
