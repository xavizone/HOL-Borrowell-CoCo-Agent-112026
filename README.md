# Borrowell Product Insights Agent HOL

Two Streamlit apps from one codebase. All data is synthetic.

| Entry point | What |
|---|---|
| `Workshop_Guide_Start.py` | Interactive guide: prompts, Snowsight routes and catch-up SQL for your `LAB_<NAME>` schema |
| `Dry_Run_Results.py` | Read-only: the same guide with the captured result of a real run under every step. No Snowflake connection needed - use it if your environment isn't ready or you fall behind |

`captured/` holds the dry-run output (`tools/capture.py` for SQL checkpoints, `tools/agent_eval.py` for the agent).
Re-capture after changing the lab: `python tools/capture.py --name DEMO --connection <conn>`.

Test both modes: `python tools/test_app.py`.
