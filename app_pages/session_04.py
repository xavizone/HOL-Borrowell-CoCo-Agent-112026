import streamlit as st

from components import (answer_key, render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_key_concepts, render_prompt, render_real_world_examples, render_references,
                        render_session_header, render_snowsight_route, render_technologies_used, render_what_why,
                        render_what_you_built)
from content import links as L
from content import story

render_session_header("Session 4", "Build the Product Insights agent", "20 min", "Cortex Agent `PRODUCT_INSIGHTS_AGENT`")
render_execution_context()
story.chapter(4)
render_what_why(
    "Create a **Cortex Agent** with two tools - Cortex Analyst over `PRODUCT_INSIGHTS_SV` for numbers and Cortex Search "
    "over the knowledge base for context - and instructions for how to read out an experiment. Then ask it Priya's and "
    "Marco's questions.",
    "One domain agent per team answers more accurately than one agent for everything. This one is for product, marketing "
    "and data science, and it's the one Workwell will call as a sub-agent.",
)

render_prompt("Prompt 4.1", "Create the agent", """Create a Cortex Agent {FQ_SCHEMA}.PRODUCT_INSIGHTS_AGENT, display name "Product Insights Agent", orchestration model claude-sonnet-4-5, with two tools:
- funnel_metrics: Cortex Analyst on {FQ_SCHEMA}.PRODUCT_INSIGHTS_SV, warehouse {WH}
- experiment_knowledge: Cortex Search on {FQ_SCHEMA}.EXPERIMENT_DOCS_SEARCH, title column title, id column doc_id, max 4 results
Orchestration instructions: use funnel_metrics for numbers and experiment_knowledge for briefs, definitions, guardrails and data issues. For an experiment readout, read the brief first, then compare both arms on CTR, approval rate, referral revenue and revenue per exposed member. Check for a known data issue before calling a sudden change real.
Response instructions: answer first, then a compact table; name the metrics and date window; revenue in CAD; say whether a guardrail was breached; never promise a member approval.
Add three sample questions. Show me the spec before creating it.""")
render_snowsight_route([
    "**AI & ML » Agents » Create agent** in `{SCHEMA}`, name `PRODUCT_INSIGHTS_AGENT`.",
    "**Orchestration**: model `claude-sonnet-4-5` (or **auto**), paste the orchestration and response instructions.",
    "**Tools » Cortex Analyst** » `PRODUCT_INSIGHTS_SV`, warehouse `{WH}`. **Tools » Cortex Search** » `EXPERIMENT_DOCS_SEARCH`.",
])
render_checkpoint("`SHOW AGENTS IN SCHEMA {FQ_SCHEMA};` lists the agent, and it appears under **AI & ML » Agents**.")

render_prompt("Prompt 4.2", "Ask Priya's and Marco's questions", """Ask {FQ_SCHEMA}.PRODUCT_INSIGHTS_AGENT these two questions with SNOWFLAKE.CORTEX.DATA_AGENT_RUN, and for each show the answer, the tools it called and the SQL it ran:
1. Read out EXP-114: did the payout-ranked carousel win? Include revenue per exposed member for both arms.
2. Offer CTR dropped sharply in late September. Is that real?""")
render_snowsight_route([
    "Open the agent in **AI & ML » Agents** » **Playground** and ask both questions.",
    "Open the trace (thinking / tool calls) to see Search, then Analyst, then the SQL.",
], sql="""SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN('{FQ_SCHEMA}.PRODUCT_INSIGHTS_AGENT',
  $${"messages":[{"role":"user","content":[{"type":"text","text":"Read out EXP-114: did the payout-ranked carousel win?"}]}]}$$)) AS response;""")
render_checkpoint("Question 2: the agent finds the **Android 5.2.0** issue. Question 1: it reads the brief and says the "
                  "**approval guardrail was breached** (60.9% → 43.3%). **But look at the revenue numbers and the SQL** - "
                  "on our test run it said revenue per exposed member went *up* by about $3.54, with referral revenue around "
                  "$2.6M per arm. Hold that thought.")
story.turn(4)

render_explanation("How the agent decides what to do", """
The orchestration model plans: it searches the brief, asks Analyst a question, Analyst writes SQL against the semantic view
and runs it, and the model writes the answer. The **instructions** are where Borrowell's analytical judgement lives -
*read the brief first*, *check for a known data issue*, *never promise approval*.
""")
render_explanation("Azure Canada Central and model choice", """
Borrowell's account is on Azure Canada Central. Claude models there need cross-region inference
(`CORTEX_ENABLED_CROSS_REGION`) - see **Azure Canada Central availability**. If it isn't enabled, use orchestration model
`auto` or one listed by `SHOW CORTEX BASE MODELS`.
""")
render_fallback(answer_key("-- Session 4", "-- Session 5:"))

render_technologies_used([
    {"name": "Cortex Agents", "icon": "smart_toy", "description": "Plans across tools (Analyst, Search, custom functions) to answer a question."},
    {"name": "Cortex Analyst", "icon": "analytics", "description": "Text-to-SQL grounded in the semantic view."},
    {"name": "DATA_AGENT_RUN", "icon": "terminal", "description": "Run an agent from SQL - the basis for tests and evals."},
])
render_key_concepts([
    {"term": "Orchestration vs response instructions", "definition": "Orchestration says *how to work* (which tool, in what order). Response says *how to answer* (format, units, what never to say)."},
    {"term": "Tool trace", "definition": "Every tool call and the SQL it ran. Reading it is how you catch an answer that sounds right and isn't."},
])
render_what_you_built(["`PRODUCT_INSIGHTS_AGENT` - funnel metrics + experiment knowledge in one conversation"])
render_real_world_examples([
    {"title": "Snowflake Intelligence", "body": "The same agent can be published to business users in Snowflake Intelligence with no extra build."},
    {"title": "Experiment readouts on demand", "body": "Every experiment with a brief in the knowledge base gets the same readout pattern, guardrails included."},
])
render_references({"Quickstarts": [L.QS_AGENTS], "Docs": [L.AGENTS, L.AGENT_CREATE, L.AGENTS_MANAGE, L.AGENT_RUN, L.CROSS_REGION]})
