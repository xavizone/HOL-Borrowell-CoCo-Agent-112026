# Borrowell | Product Insights Agent hands-on lab | Before you start

90 minutes, hands-on, Tuesday 10 November, 2:30-4:00 PM (York St, Toronto, and Zoom). Please do the first section the day before.

## Things to do

**The day before (10-15 minutes)**

1. **Log in to Snowflake** in a browser with your usual sign-in (SSO or MFA). If it fails, tell Archana now, not on the day.
2. **Install and sign in to CoCo** - Cortex Code Desktop (macOS or Windows) or the CoCo CLI. Either works for every step. Connect it to Borrowell's Snowflake account.
   Download: https://www.snowflake.com/en/product/snowflake-coco/downloads/ - CLI: `curl -LsS https://ai.snowflake.com/static/cc-scripts/install.sh | sh`.
   Step-by-step instructions and fixes are on the guide's **Install CoCo Desktop and CLI** page.
3. **Run this test prompt in CoCo:** *"What is my current user, role and warehouse? Run select current_user(), current_role(), current_warehouse()."* If you get an answer, CoCo is working.
4. **Confirm your lab name** with Archana (usually your first name, for example `ARCHANA`). It names your schema `BORROWELL_AGENT_LAB.LAB_<NAME>` and your role `PI_LAB_<NAME>`.
5. **Optional, for Session 5:** install the Snowflake CLI (`snow --version`) and Python 3.10+ so you can run the evaluation script yourself. If you don't, the facilitator runs it on screen.

**On the day (5 minutes before)**

1. Open the lab guide and type your lab name into the sidebar box. Every prompt updates to your schema and role.
2. In CoCo, switch to your lab role and warehouse: `USE ROLE PI_LAB_<NAME>; USE SECONDARY ROLES NONE; USE WAREHOUSE PI_LAB_WH;`
3. Run **Prompt 1.1**. You should see 8 tables in `BORROWELL_AGENT_LAB.DATA`.
4. Not on the attendee list? Tell the facilitator - a spare workspace takes about a second to hand over.

## Things to know

- **The question.** Priya, a product manager on Marketplace Growth, asks: *"EXP-114 ranked offers by payout instead of relevance. CTR went up. Can we ship it? And why did CTR crash in late September?"* You'll build the agent that answers both - correctly.
- **What you build.** In your own schema: curated views, a semantic view with governed CTR / approval rate / revenue, a Cortex Search service over experiment docs, a Cortex Agent with both as tools, an evaluation, and a Snowflake-managed MCP server that Workwell could call. Stretch: an offer-ranking function that ranks by expected revenue (approval odds x payout).
- **You get your own workspace.** Schema `LAB_<NAME>` is yours; you own everything in it. The shared telemetry in `DATA` is read-only.
- **The data is synthetic.** Members, partners, offers, events and experiments are generated for the lab. No real Borrowell or member data is used, and partner names are fictional.
- **The data has realistic traps.** Bot traffic, internal test accounts and an app release that double-sends impressions. Finding them is part of the lab.
- **The agent will get one answer wrong.** It's a real failure, not a staged one: a cross-table question the first semantic view doesn't handle. Session 5 catches it with an evaluation and fixes it in the semantic layer - the same kind of problem that paused Workwell.
- **CoCo first, SQL always.** Every step is a CoCo prompt, and each has a *Behind? Run this* box with the exact SQL that was tested.
- **Read before you approve.** CoCo shows the SQL before it runs it. You're in Borrowell's real account - approve deliberately.
- **Cost is capped.** One XSMALL warehouse (`PI_LAB_WH`) with a 10-credit resource monitor.
- **Models.** The agent uses `claude-sonnet-4-5`. Borrowell's account is on Azure Canada Central, so this needs cross-region inference enabled by the admin (see the admin questionnaire).

## What to expect

| Minutes | Session | You will |
|---|---|---|
| 0-10 | 1. Explore the telemetry | Profile the offers funnel with CoCo and find why CTR "dropped" |
| 10-30 | 2. Build the semantic layer | Curated views + a semantic view with one definition of CTR, approval rate and revenue |
| 30-40 | 3. Add knowledge with Search | Index experiment briefs, metric definitions and known data issues |
| 40-60 | 4. Build the agent | Create the Product Insights agent and ask Priya's questions |
| 60-75 | 5. Evaluate and connect Workwell | Run a 6-question eval, catch a wrong answer, fix it, create the MCP server |
| 75-90 | Stretch: approval-aware ranking | Rank offers by expected revenue and project the revenue lift |

- **CoCo's output varies.** The same prompt can produce slightly different SQL or wording. The checkpoint under each prompt says what "good" looks like.
- **Falling behind is fine.** Every session has a catch-up box, and the facilitator can reset your workspace in seconds.
- **Afterwards:** the guide stays online, and your schema is kept until the admin runs teardown.
