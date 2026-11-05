import streamlit as st

from components import (answer_key, render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_key_concepts, render_prompt, render_real_world_examples, render_references,
                        render_session_header, render_snowsight_route, render_technologies_used, render_what_why,
                        render_what_you_built)
from content import links as L
from content import story
import dry_run

render_session_header("Session 3", "Add knowledge with Cortex Search", "10 min",
                      "Cortex Search service `EXPERIMENT_DOCS_SEARCH`")
render_execution_context()
story.chapter(3)
render_what_why(
    "Index the product data science knowledge base (`DATA.EXPERIMENT_DOCS`: experiment briefs, metric definitions, "
    "known data issues, payout policy) with **Cortex Search**, then test it.",
    "Workwell already searches Confluence and Google Docs. Search inside Snowflake keeps the knowledge next to the data "
    "and under the same access control, so the agent can answer *why*, not just *what*.",
)

render_prompt("Prompt 3.1", "Create and test the search service", """Create a Cortex Search service {FQ_SCHEMA}.EXPERIMENT_DOCS_SEARCH on BORROWELL_AGENT_LAB.DATA.EXPERIMENT_DOCS:
search the body column, with doc_type, experiment_id and title as attributes, warehouse {WH}, target lag 1 day.
Then test it with the query "why did CTR drop in late September" and show the top 3 titles and doc types.""")
render_snowsight_route([
    "**AI & ML » Cortex Search** » **Create** in `{SCHEMA}`, source table `BORROWELL_AGENT_LAB.DATA.EXPERIMENT_DOCS`.",
    "Search column `BODY`; attributes `DOC_TYPE`, `EXPERIMENT_ID`, `TITLE`; warehouse `{WH}`; target lag 1 day.",
    "Open the service » **Playground** and search *why did CTR drop in late September*.",
], sql="""SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('{FQ_SCHEMA}.EXPERIMENT_DOCS_SEARCH',
  '{"query": "why did CTR drop in late September", "columns": ["title", "doc_type"], "limit": 3}')):results;""")
render_checkpoint("Top hit: **Known data issue: Android 5.2.0 duplicate impressions**, then the EXP-114 brief and the CTR metric definition.")
dry_run.show("s3_search")
story.turn(3)

render_explanation("Hybrid search, no embeddings to manage", """
Cortex Search combines vector and keyword search and handles embedding and refresh itself. `TARGET_LAG` controls how fresh
the index is. Attributes can be used as filters - the agent can ask for `doc_type = 'data_issue'` only.
""")
render_explanation("Seeing `Insufficient privileges ... CHANGE_TRACKING`?", """
The service builds an incremental index, so its source table needs change tracking. The admin turns it on in `01_data.sql`
(`ALTER TABLE BORROWELL_AGENT_LAB.DATA.EXPERIMENT_DOCS SET CHANGE_TRACKING = TRUE;`). Ask the facilitator.
""")
render_fallback(answer_key("-- Session 3", "-- Session 4"))

render_technologies_used([
    {"name": "Cortex Search", "icon": "manage_search", "description": "Managed hybrid search over text in a table, refreshed to a target lag."},
    {"name": "SEARCH_PREVIEW", "icon": "preview", "description": "Test a service from SQL before you give it to an agent."},
])
render_key_concepts([
    {"term": "Attributes", "definition": "Columns the service can filter on (doc type, experiment id). They make answers precise without a separate index."},
])
render_what_you_built(["`EXPERIMENT_DOCS_SEARCH` - briefs, definitions and data issues, searchable next to the data"])
render_real_world_examples([
    {"title": "Confluence and Google Drive", "body": "Openflow connectors can land Confluence pages or Drive docs in a table for the same kind of service."},
    {"title": "A data issues log that's actually read", "body": "Every known issue the team writes up becomes something the agent checks before it calls a change real."},
])
render_references({"Docs": [L.SEARCH, L.SEARCH_CREATE, L.SEARCH_PREVIEW]})
