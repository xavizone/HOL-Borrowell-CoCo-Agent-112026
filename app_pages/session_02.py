import streamlit as st

from components import (answer_key, render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_key_concepts, render_prompt, render_real_world_examples, render_references,
                        render_session_header, render_snowsight_route, render_technologies_used, render_what_why,
                        render_what_you_built)
from content import links as L
from content import story

render_session_header("Session 2", "Build the semantic layer", "20 min",
                      "Curated views + semantic view `PRODUCT_INSIGHTS_SV`")
render_execution_context()
story.chapter(2)
render_what_why(
    "Have CoCo build curated views that remove bots, test accounts and duplicate events, then a **semantic view** with "
    "governed metrics: impressions, clicks, CTR, exposed members, applications, approval rate and referral revenue.",
    "A semantic view makes *\"what's our CTR?\"* return the same number in Cortex Analyst, the agent, Workwell and a "
    "notebook. Borrowell's business logic lives in Looker today - this is where it moves.",
)

render_prompt("Prompt 2.1", "Curated views", """In {FQ_SCHEMA}, create views over BORROWELL_AGENT_LAB.DATA that a product data scientist can trust:
1. MEMBERS_V - members where is_test is false, with their EXP-114 variant from EXPERIMENT_ASSIGNMENTS (default 'not assigned') as exp114_variant.
2. OFFER_EVENTS_V - TELEMETRY_EVENTS for those members only, no bots, one row per client_event_id.
3. APPLICATIONS_V - applications from those members.
4. OFFERS_V - all partner offers.
Add a comment to each view saying what it removes. Show me the SQL before running it.""")
render_snowsight_route(["Open a worksheet in `{SCHEMA}` and run the *Behind?* SQL below (views part)."])
render_checkpoint("`SHOW VIEWS IN SCHEMA {FQ_SCHEMA};` lists 4 views. `OFFER_EVENTS_V` has about 491K rows.")

render_prompt("Prompt 2.2", "The semantic view", """/semantic_studio Create a semantic view {FQ_SCHEMA}.PRODUCT_INSIGHTS_SV over MEMBERS_V, OFFERS_V, OFFER_EVENTS_V and APPLICATIONS_V.
- Relationships: OFFER_EVENTS_V and APPLICATIONS_V to MEMBERS_V (member_id) and to OFFERS_V (offer_id); the events/applications side is the left (many) table.
- Metrics: impressions and clicks (COUNT DISTINCT client_event_id by event_type), ctr, exposed_members (distinct members with an impression), submitted_applications, approved_applications, approval_rate, referral_revenue (CAD).
- Dimensions: province, score_band, is_newcomer, exp114_variant, partner_name, product_type, offer_name, surface, platform, app_version, slot_position, event_date, submitted_date.
- Synonyms: click-through rate, approvals, revenue, experiment arm. Add a description to every metric.""")
render_snowsight_route([
    "**AI & ML » Cortex Analyst** » **Create new** » Semantic view in `{SCHEMA}`, add the four views.",
    "Add the four relationships, then the metrics and dimensions above.",
    "Ask in the playground: *\"weekly CTR from August to October 2026\"*.",
])

render_prompt("Prompt 2.3", "Prove it", """Using only {FQ_SCHEMA}.PRODUCT_INSIGHTS_SV, show weekly CTR from August to October 2026 next to the naive weekly CTR from raw BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS rows. Did CTR really drop in late September?""")
render_snowsight_route(["Run the query below in a worksheet."], sql="""SELECT * FROM SEMANTIC_VIEW({FQ_SCHEMA}.PRODUCT_INSIGHTS_SV
  DIMENSIONS DATE_TRUNC('week', events.event_date) AS week
  METRICS events.impressions, events.clicks, events.ctr) ORDER BY week;""")
render_checkpoint("Governed CTR is **flat at about 6.0%** every week (5.7-6.3%). Naive CTR sits around 7.8% and appears to "
                  "fall about 12% from the week of 21 Sep. One definition, and the September \"crash\" is gone.")
story.turn(2)

render_explanation("Why curated views first, then a semantic view", """
The views fix **rows** (which events count). The semantic view fixes **definitions** (how a metric is computed, what it joins to,
what it's called). Keep row-level cleaning in views or dbt models and business definitions in the semantic view - the same
split as Borrowell's planned silver and gold layers.
""")
render_explanation("Reading the semantic view YAML", """
`tables` declare a base table, a primary key, dimensions, facts and metrics. `relationships` declare many-to-one joins.
`custom_instructions` are hints Cortex Analyst reads when it writes SQL. Query it directly with
`SELECT * FROM SEMANTIC_VIEW(... DIMENSIONS ... METRICS ...)`.
""")
render_fallback(answer_key("-- Session 2a", "-- Session 3"))

render_technologies_used([
    {"name": "Semantic views", "icon": "schema", "description": "Governed metrics, dimensions and joins, stored as a Snowflake object."},
    {"name": "SEMANTIC_VIEW() query", "icon": "query_stats", "description": "Query metrics by dimension from SQL - the same definitions the agent uses."},
    {"name": "CoCo semantic view authoring", "icon": "smart_toy", "description": "/semantic_studio writes, validates and fixes the YAML."},
])
render_key_concepts([
    {"term": "Metric vs fact vs dimension", "definition": "A **metric** is an aggregate (CTR). A **fact** is a row-level number or key (payout, member_id). A **dimension** is what you group or filter by (score band, surface)."},
    {"term": "Primary key on the right-hand table", "definition": "Each relationship is many-to-one. The right-hand table (members, offers) must declare its primary key so Analyst knows joins won't multiply rows."},
])
render_what_you_built([
    "`MEMBERS_V`, `OFFER_EVENTS_V`, `APPLICATIONS_V`, `OFFERS_V` - no bots, no test accounts, no duplicate events",
    "`PRODUCT_INSIGHTS_SV` - one definition of CTR, approval rate and referral revenue",
])
render_real_world_examples([
    {"title": "LookML to semantic views", "body": "The same pattern applies to Borrowell's LookML explores - see the CoCo migration session."},
    {"title": "One CTR everywhere", "body": "Looker, Workwell and notebooks can all read the same semantic view, so the number stops depending on who asked."},
])
render_references({"Quickstarts": [L.QS_SV, L.QS_SV_BP], "Docs": [L.SV_OVERVIEW, L.SV_CREATE, L.SV_QUERY, L.ANALYST]})
