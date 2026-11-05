# Borrowell | Product Insights Agent lab | Admin pre-flight questionnaire

For the Borrowell Snowflake admin (Archana or delegate). Answers by **Thu 5 Nov** (prep call, 2:00 PM); setup by **Mon 9 Nov**.

| # | When | Question | Why | How to check |
|---|---|---|---|---|
| 1 | T-5 | Who has **ACCOUNTADMIN** and can run setup (~5 min) and teardown? | Setup creates roles, a warehouse, a resource monitor and a database | - |
| 2 | T-5 | Final **attendee list**: each person's exact Snowflake **user name** and a lab name (e.g. first name) | Each attendee gets role `PI_LAB_<NAME>` and schema `LAB_<NAME>` | `SHOW USERS LIKE '<user>';` |
| 3 | T-5 | Is **cross-region inference** enabled, or can it be for the lab? | Azure Canada Central: `claude-sonnet-4-5` (agent orchestration) needs it | `SHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;` |
| 4 | T-5 | Do attendees' roles reach **`SNOWFLAKE.CORTEX_USER`**? Is CoCo allowed for all of them (including the GenAI Ops team)? | Cortex Analyst, Search, Agents and CoCo | Setup grants `CORTEX_USER` to `PI_LAB_ATTENDEE`; check any CoCo allow-list or RSS policy |
| 5 | T-5 | Any **network policy, allowed-model list or Cortex feature policy** that could block CoCo, agents or MCP servers? | Avoid surprises on the day | `SHOW NETWORK POLICIES;` `SHOW PARAMETERS LIKE 'CORTEX_MODELS_ALLOWLIST' IN ACCOUNT;` |
| 6 | T-5 | Can we use the name **`BORROWELL_AGENT_LAB`** (database) and **`PI_LAB_WH`** (warehouse)? | Isolated, one `DROP DATABASE` to remove | `SHOW DATABASES LIKE 'BORROWELL_AGENT_LAB';` |
| 7 | T-3 | Run setup (`sql/00`, `01`, `02` + the attendee call). Send back `V_ROSTER` | Confirms every attendee is ready | `SELECT * FROM BORROWELL_AGENT_LAB.ADMIN.V_ROSTER;` |
| 8 | T-1 | Every attendee ran the CoCo test prompt | No setup time lost on the day | Attendee prep sheet, step 3 |
| 9 | After | When should teardown run? | Schemas stay until then | `sql/98_teardown.sql` |

**Cost:** one XSMALL warehouse with a 10-credit resource monitor (suspends at 100%). A full run of the lab used well under 1 credit of warehouse time per attendee on a test account; Cortex usage (Analyst, Search, agent calls) is billed separately and is small for ~10 people.
