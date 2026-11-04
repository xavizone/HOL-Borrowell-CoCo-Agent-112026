import streamlit as st

from components import (answer_key, render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_key_concepts, render_prompt, render_real_world_examples, render_references,
                        render_session_header, render_snowsight_route, render_technologies_used, render_what_why,
                        render_what_you_built, doc_file)
from content import links as L
from content import story

render_session_header("Session 5", "Evaluate, fix, and hand it to Workwell", "15 min",
                      "Eval run, `EXP114_MEMBER_OUTCOMES_V`, MCP server `PRODUCT_INSIGHTS_MCP`")
render_execution_context()
story.chapter(5)
render_what_why(
    "Run a six-question **evaluation** that checks the agent's answers against governed numbers from the semantic view. "
    "Find the one that's wrong, fix it **in the semantic layer**, re-run, and expose the agent to Workwell through a "
    "**Snowflake-managed MCP server**.",
    "\"Inaccurate answers\" is why Workwell was paused. An eval turns *trust me* into a pass rate you can re-run on every "
    "change - and the fix lives in the semantic layer, where every consumer gets it.",
)

render_prompt("Prompt 5.1", "Evaluate the agent", """Run tools/agent_eval.py --name {NAME} (download it below) with my snow connection. It asks {FQ_SCHEMA}.PRODUCT_INSIGHTS_AGENT six questions with DATA_AGENT_RUN and checks each answer against {FQ_SCHEMA}.PRODUCT_INSIGHTS_SV under the same role.
For every failing case, show me the SQL the agent generated and explain exactly why the number is wrong.""")
st.download_button("Download tools/agent_eval.py", data=doc_file("tools/agent_eval.py"), file_name="agent_eval.py",
                   icon=":material/download:", key="dl_eval")
st.code("uv run --with snowflake-cli python agent_eval.py --name {NAME} --connection <your-connection>"
        .replace("{NAME}", st.session_state.get("lab_name", "DEMO").upper()), language="bash")
render_snowsight_route(["No CLI? Ask question 1 again in the agent **Playground**, open the trace, and read the SQL "
                        "it ran against the checkpoint below."])
render_checkpoint("Before the fix, **E1 fails** (E5 needs the stretch - expect 4/6). The agent's SQL joins `events` to "
                  "`applications` on member and offer, so each application is counted once per event row: referral "
                  "revenue about **$2.6M per arm** when the whole window earned about $700K.")

render_prompt("Prompt 5.2", "Fix it in the semantic layer", """The EXP-114 readout joined events to applications, which fans out revenue. Fix it in the semantic layer:
1. Create {FQ_SCHEMA}.EXP114_MEMBER_OUTCOMES_V with one row per assigned member: variant, score_band, impressions, clicks, applications, approvals and referral_revenue_cad inside 2026-08-15 to 2026-10-15.
2. Add it to PRODUCT_INSIGHTS_SV as table exp114 (dimension arm) with metrics exp_assigned_members, exp_exposed_members, exp_ctr, exp_approval_rate, exp_referral_revenue and exp_revenue_per_exposed_member.
3. Replace the custom instructions: for any EXP-114 readout use only the exp114 metrics grouped by arm, and never join events and applications in one query.
Then re-run the eval.""")
render_snowsight_route(["Run the *Behind?* SQL, then ask the agent question 1 again."], sql="""SELECT * FROM SEMANTIC_VIEW({FQ_SCHEMA}.PRODUCT_INSIGHTS_SV DIMENSIONS exp114.arm
  METRICS exp114.exp_ctr, exp114.exp_approval_rate, exp114.exp_referral_revenue, exp114.exp_revenue_per_exposed_member);""")
render_checkpoint("""Re-run: **E1-E4 and E6 pass** (5/6 without the stretch).

| Arm | CTR | Approval rate | Referral revenue | Revenue per exposed member |
|---|---|---|---|---|
| control | 5.81% | 60.9% | 348,865 CAD | 37.30 CAD |
| treatment | 6.33% | 43.3% | 353,235 CAD | 36.92 CAD |

CTR +9%, approvals **-17.6 points** (guardrail: -5), revenue per exposed member **down**. Don't ship.""")

render_prompt("Prompt 5.3", "Hand it to Workwell", """Create a Snowflake-managed MCP server {FQ_SCHEMA}.PRODUCT_INSIGHTS_MCP with one CORTEX_AGENT_RUN tool named product_insights pointing at {FQ_SCHEMA}.PRODUCT_INSIGHTS_AGENT, annotated read-only (readOnlyHint true, destructiveHint false).
Then show me the MCP endpoint URL Workwell would call, and the grants a Workwell service role needs.""")
render_snowsight_route(["Run the SQL below, then `SHOW MCP SERVERS IN SCHEMA {FQ_SCHEMA};`."],
                       sql=answer_key("-- Session 5:", "-- Session 5b").split("\n\n", 1)[1])
render_checkpoint("""`SHOW MCP SERVERS` lists `PRODUCT_INSIGHTS_MCP`. Workwell calls
`https://<account>.snowflakecomputing.com/api/v2/databases/BORROWELL_AGENT_LAB/schemas/{SCHEMA}/mcp-servers/PRODUCT_INSIGHTS_MCP`
as a service user whose role has USAGE on the MCP server and the agent.""")
story.turn(5)

render_explanation("What a fan-out is, and why the agent fell into it", """
Events have one row per impression or click; applications have one row per application. Joining them on member and offer
repeats each application once per matching event, so `SUM(revenue)` multiplies. Every metric in the semantic view was right
on its own - the bug was a **cross-table question**. The fix gives that question its own correct grain (one row per member)
and tells Analyst to use it. Every consumer of the semantic view gets the fix, not just this agent.
""")
render_explanation("How the eval decides pass or fail", """
- **Numeric cases** (E1, E3, E4, E5): the expected number comes from the semantic view itself, queried with your role.
- **Behaviour cases** (E2, E6): required content (the Android 5.2.0 issue) or a refusal (no promise of approval).
- **Any tool that errored and never recovered fails the case** - an agent that quietly improvises when a tool breaks is a
  wrong answer, even if the text looks right. (We hit exactly that while building the stretch.)
- **Run it more than once.** Agent answers vary run to run. In our dry run E5 passed 2 of 3 times (one answer left out
  an amount). Judge an agent on a pass *rate* over repeated runs, not a single run.
""")
render_fallback(answer_key("-- Session 5b", "-- Stretch:"))

render_technologies_used([
    {"name": "Agent evaluation", "icon": "rule", "description": "Real questions + governed expected answers, re-run on every change. AI Observability adds LLM judges and traces."},
    {"name": "Snowflake-managed MCP server", "icon": "hub", "description": "Expose agents, Analyst and Search as MCP tools to Workwell or any MCP client."},
])
render_key_concepts([
    {"term": "Fan-out", "definition": "A join that repeats rows on one side, so sums and counts on that side multiply."},
    {"term": "Grain", "definition": "What one row means (one event, one application, one member). A readout should be computed at the grain of the question."},
    {"term": "MCP", "definition": "Model Context Protocol - a standard way for an assistant like Workwell to discover and call tools. Snowflake hosts the server; access is the caller's Snowflake role."},
])
render_what_you_built([
    "An eval that checks the agent against governed numbers",
    "`EXP114_MEMBER_OUTCOMES_V` + the `exp114` table in `PRODUCT_INSIGHTS_SV` - a correct readout grain",
    "`PRODUCT_INSIGHTS_MCP` - the agent, callable from Workwell",
])
render_real_world_examples([
    {"title": "Eval in CI", "body": "Run agent_eval.py in the pipeline that deploys semantic view changes - a failing eval blocks the deploy."},
    {"title": "Workwell sub-agents", "body": "One MCP server per domain agent (product insights, go-to-market, finance) keeps each one accurate and governed by the caller's role."},
])
render_references({"Quickstarts": [L.QS_AGENT_EVAL, L.QS_AI_OBS], "Docs": [L.AI_OBS, L.AGENT_RUN, L.MCP, L.MCP_CREATE]})
