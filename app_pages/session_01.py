import streamlit as st

from components import (render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_key_concepts, render_prompt, render_real_world_examples, render_references,
                        render_session_header, render_snowsight_route, render_technologies_used, render_what_why,
                        render_what_you_built)
from content import links as L
from content import story
import dry_run

render_session_header("Session 1", "Explore the telemetry", "10 min", "Nothing yet - you're profiling `BORROWELL_AGENT_LAB.DATA`")
render_execution_context()
story.chapter(1)
render_what_why(
    "Use CoCo to discover the shared offers telemetry, profile the funnel (impressions, clicks, applications) and spot "
    "what would make a quick answer wrong - before you define a single metric.",
    "Workwell was paused because answers from raw tables were inaccurate. The fastest way to see why is to let CoCo "
    "profile the data and find the traps a dashboard query would miss.",
)

render_prompt("Prompt 1.1", "Check your setup and find the data", """Use role {ROLE}, secondary roles none, warehouse {WH} and schema {FQ_SCHEMA}.
Then run select current_user(), current_role(), current_warehouse(), current_schema(), and list the tables in BORROWELL_AGENT_LAB.DATA with their row counts and comments.""")
render_snowsight_route([
    "Open **Catalog » Database Explorer** » `BORROWELL_AGENT_LAB` » `DATA`.",
    "Click each table to see its columns and comments; `TELEMETRY_EVENTS` » **Data Preview**.",
], sql="SELECT table_name, row_count, comment FROM BORROWELL_AGENT_LAB.INFORMATION_SCHEMA.TABLES\nWHERE table_schema = 'DATA' ORDER BY 1;")
render_checkpoint("You see **8 tables** in `DATA`. `TELEMETRY_EVENTS` has about **586K** rows, `APPLICATIONS` about 12K, `MEMBERS` 20,000.")
dry_run.show("s1_tables")

render_prompt("Prompt 1.2", "Profile the offers funnel", """Profile BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS for a product data scientist:
- event types with row counts and distinct client_event_id counts
- how much traffic is flagged is_bot
- how many events come from MEMBERS where is_test is true
- weekly offer CTR (offer_click rows / offer_impression rows) from August to October 2026, computed the naive way on raw rows
What looks suspicious?""")
render_snowsight_route(["Open a worksheet with role `{ROLE}` and warehouse `{WH}` and run the SQL below."],
                       sql="""SELECT event_type, COUNT(*) rows_collected, COUNT(DISTINCT client_event_id) distinct_events,
       COUNT_IF(is_bot) bot_rows
FROM BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS GROUP BY 1 ORDER BY 2 DESC;""")
render_checkpoint("CoCo notices three things: impression **rows outnumber distinct `client_event_id`s** (517K vs 483K), "
                  "**bots** account for about 6K clicks, and **test accounts** are in the data. Naive CTR is about **7.4-8.0%**.")
dry_run.show("s1_profile")

render_prompt("Prompt 1.3", "Is the September drop real?", """Naive CTR drops from about 7.8% to 6.8% around 2026-09-21.
Break offer_impression rows down by platform, app_version and surface before and after that date, and check whether the same client_event_id appears more than once. Is the drop real?""")
render_checkpoint("The drop comes from **Android `5.2.0` on the `dashboard` surface**, which sends every impression twice "
                  "(same `client_event_id`, ~180 ms apart). Count distinct events and the drop disappears - Marco's campaigns are safe.")
dry_run.show("s1_dups")
story.turn(1)

render_explanation("The three data issues in this lab (all realistic)", """
| Issue | Effect on a naive query | Fix |
|---|---|---|
| Bot / crawler traffic (`is_bot`, `member_id` NULL) | Inflates clicks and CTR | Exclude bots and logged-out rows |
| Internal QA / test accounts (`MEMBERS.is_test`) | Click and apply far more than real members | Exclude test members |
| Android 5.2.0 double-fires dashboard impressions | Impressions jump, CTR appears to fall from 21 Sep | Count DISTINCT `client_event_id` |

Each one is written up in `DATA.EXPERIMENT_DOCS`, the knowledge base the agent searches in Session 3.
""")
render_fallback("""SELECT platform, app_version, surface, event_date >= '2026-09-21' AS after_sep21,
       COUNT(*) rows_collected, COUNT(DISTINCT client_event_id) distinct_events
FROM BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS WHERE event_type = 'offer_impression'
GROUP BY ALL HAVING rows_collected <> distinct_events ORDER BY 1, 2, 3;""")

render_technologies_used([
    {"name": "CoCo data discovery", "icon": "travel_explore", "description": "CoCo reads catalog metadata and column comments, writes the profiling SQL and explains what it finds."},
    {"name": "Column comments", "icon": "notes", "description": "Every column in DATA has a comment. CoCo, Cortex Analyst and the agent all read them."},
])
render_key_concepts([
    {"term": "client_event_id", "definition": "The id the app generates for an event. If the app sends an event twice, the collector gives each row a new `event_id` but the `client_event_id` stays the same - so it's the one to count."},
    {"term": "CTR", "definition": "Click-through rate = distinct offer clicks / distinct offer impressions, for real members. A leading indicator only - Borrowell earns referral revenue on **approvals**."},
])
render_what_you_built(["A profile of the offers funnel and the three data issues behind a wrong CTR"])
render_real_world_examples([
    {"title": "Experiment QA before a readout", "body": "Run Prompt 1.2 on any experiment's telemetry before anyone looks at lift."},
    {"title": "Release monitoring", "body": "A data metric function on raw vs distinct counts would have flagged Android 5.2.0 the day it shipped."},
])
render_references({"Quickstarts": [L.QS_COCO_DESKTOP, L.QS_COCO_DE], "Docs": [L.COCO, L.COCO_DESKTOP]})
