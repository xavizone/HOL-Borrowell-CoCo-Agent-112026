import streamlit as st

from components import (answer_key, render_checkpoint, render_execution_context, render_explanation, render_fallback,
                        render_key_concepts, render_prompt, render_real_world_examples, render_references,
                        render_session_header, render_snowsight_route, render_technologies_used, render_what_why,
                        render_what_you_built)
from content import links as L
from content import story
import dry_run

render_session_header("Stretch", "Approval-aware offer ranking", "15 min (or take-home)",
                      "`APPROVAL_ODDS`, `RECOMMEND_OFFERS` (+ `_TOOL`), `RANKING_POLICY_COMPARISON`, an agent tool")
render_execution_context()
story.chapter(6)
render_what_why(
    "Learn approval odds by score band and offer from pre-experiment applications, rank offers by **expected revenue = "
    "approval odds x payout**, compare three ranking policies, and give the agent a `recommend_offers` tool.",
    "This is the business outcome: more referral revenue **and** fewer declined applications - fewer hard inquiries on "
    "members' files. Better matches for members, more revenue for Borrowell.",
)

render_prompt("Prompt S.1", "Approval odds and a ranking function", """In {FQ_SCHEMA}:
1. Create table APPROVAL_ODDS: approval rate by score_band_idx and offer_id from APPLICATIONS_V joined to MEMBERS_V, for applications submitted before 2026-08-15 (pre-experiment).
2. Create a SQL table function RECOMMEND_OFFERS(P_MEMBER_ID NUMBER, P_TOP_N NUMBER) that ranks every offer for that member by approval odds x payout_cad. Use APPROVAL_ODDS when there are at least 20 applications, otherwise the band-gap prior from the "Score bands and partner targeting" doc (78% / 55% / 8% / 2%). Return rnk, offer_id, offer_name, partner_name, payout_cad, approval_odds and expected_revenue_cad as FLOAT columns.
3. Show the result for member 42 next to the top 3 offers the payout_ranked policy in DATA.OFFER_RANKINGS shows them.""")
render_checkpoint("Member 42 (Good band): payout ranking leads with the **5-Year Fixed Mortgage** ($450 - a reach offer, ~8% odds). "
                  "Approval-aware leads with **Mortgage Renewal** (52% x $320 = **$165.33**), then Personal Loan ($147.27) and Auto Loan ($135.38).")
dry_run.show("st_ranking")

render_prompt("Prompt S.2", "Project the business outcome", """Create view {FQ_SCHEMA}.RANKING_POLICY_COMPARISON comparing three policies for the top 4 carousel slots - relevance and payout_ranked from BORROWELL_AGENT_LAB.DATA.OFFER_RANKINGS, and approval_aware (top 4 by expected revenue for each score band, same odds as RECOMMEND_OFFERS).
Weight by how many members are in each band and report expected_revenue_per_application_cad and avg_approval_odds per policy.""")
render_snowsight_route(["Run `SELECT * FROM {FQ_SCHEMA}.RANKING_POLICY_COMPARISON ORDER BY 2 DESC;` and chart it."])
render_checkpoint("""| Policy | Expected revenue per application | Avg approval odds |
|---|---|---|
| approval_aware | 126.14 CAD | 65.9% |
| relevance (today) | 113.41 CAD | 59.3% |
| payout_ranked (EXP-114) | 98.12 CAD | 38.3% |

About **+11%** over today's ranking and **+29%** over payout ranking, with members more likely to be approved.""")
dry_run.show("st_policy")

render_prompt("Prompt S.3", "Give the agent the tool", """Agent custom tools call scalar functions, so first create {FQ_SCHEMA}.RECOMMEND_OFFERS_TOOL(P_MEMBER_ID NUMBER, P_TOP_N NUMBER) RETURNS ARRAY that returns the RECOMMEND_OFFERS rows as an array of objects, ordered by rnk.
Then update {FQ_SCHEMA}.PRODUCT_INSIGHTS_AGENT: keep both tools and add a generic tool recommend_offers backed by function {FQ_SCHEMA}.RECOMMEND_OFFERS_TOOL (inputs p_member_id and p_top_n, warehouse {WH}). Tell it to report the tool's rows exactly - no recomputing with funnel_metrics - to describe approval odds as historical rates, and never to promise approval.
Ask it "Which 3 offers should we show member 42, and why?", then re-run the eval.""")
render_snowsight_route([
    "**AI & ML » Agents** » `PRODUCT_INSIGHTS_AGENT` » **Edit** » **Tools » Custom tools**.",
    "Resource type **Function** » `RECOMMEND_OFFERS_TOOL`, warehouse `{WH}`, describe both parameters.",
    "Ask the question in the Playground and check the trace: `recommend_offers` should return rows, not an error.",
])
render_checkpoint("The trace shows `recommend_offers` returning 3 rows and the answer quotes them ($165.33, $147.27, $135.38). Eval: **6/6**.")
dry_run.show("st_tool")
dry_run.show("s5_eval_after", "Dry-run result: the final eval")
story.turn(6)
story.epilogue()

render_explanation("Why the tool is a scalar wrapper (a real bug we hit)", """
On our first run, `recommend_offers` pointed straight at the table function and failed with *Unknown user-defined function*.
The agent didn't stop - it quietly recomputed odds with Analyst over all dates and answered with different numbers and a
different third offer. The answer *looked* right. A strict eval (exact rows and amounts, and no unrecovered tool errors)
caught it. `RECOMMEND_OFFERS_TOOL` returns the same rows as an ARRAY, which a custom tool can call.
""")
render_explanation("What this projection is - and isn't", """
It's an **expected-value projection** from historical approval rates, on synthetic data - not a measured result. The real next
step is an experiment: approval-aware vs relevance, primary metric revenue per exposed member, guardrail approval rate. The
agent can read that one out too.
""")
render_explanation("Responsible ranking", """
Approval odds are a historical rate for a score band, not a prediction for a person. Check results by province and newcomer
status before shipping, keep a relevance floor so members always see something they qualify for, and never present odds as a promise.
""")
render_fallback(answer_key("-- Stretch:"))

render_technologies_used([
    {"name": "Custom agent tools", "icon": "function", "description": "Any scalar UDF or stored procedure can be an agent tool (type generic)."},
    {"name": "SQL table functions", "icon": "table_chart", "description": "Ranking logic as a governed, reusable object the app and the agent share."},
])
render_key_concepts([
    {"term": "Expected revenue", "definition": "Approval odds x payout. A $450 offer at 8% odds is worth $36; a $320 offer at 52% is worth $165."},
    {"term": "Reach offer", "definition": "An offer above the member's score band. High payout, low approval odds, and a hard inquiry on decline."},
])
render_what_you_built([
    "`APPROVAL_ODDS` - learned from pre-experiment applications",
    "`RECOMMEND_OFFERS` and `RECOMMEND_OFFERS_TOOL` - ranking by expected revenue",
    "`RANKING_POLICY_COMPARISON` - the projected revenue lift",
    "`recommend_offers` - a custom tool on the Product Insights agent",
])
render_real_world_examples([
    {"title": "The next experiment", "body": "Approval-aware vs relevance ranking, read out by the same agent with the same eval guarding it."},
    {"title": "\"Why am I seeing this offer?\"", "body": "The same function can feed member-facing explanations in the app - consistent with what the agent tells the team."},
])
render_references({"Docs": [L.AGENTS_MANAGE, L.AGENT_CREATE]})
