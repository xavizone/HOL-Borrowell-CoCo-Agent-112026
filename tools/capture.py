"""capture.py - run the lab's checkpoint queries as one attendee and write captured/results.json
for the static (read-only) guide. Usage: python3 tools/capture.py --name DEMO --connection XPRADEES_AWS01
Co-authored with CoCo
"""
import argparse
import json
import subprocess
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True)
ap.add_argument("--connection", default=None)
args = ap.parse_args()
N = args.name.upper()
S = f"BORROWELL_AGENT_LAB.LAB_{N}"
PREFIX = f"USE ROLE PI_LAB_{N}; USE SECONDARY ROLES NONE; USE WAREHOUSE PI_LAB_WH; USE SCHEMA {S};"


def sql(q):
    cmd = ["snow", "sql", "--format", "json", "-q", PREFIX + q]
    if args.connection:
        cmd[2:2] = ["-c", args.connection]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600, check=True)
    d = json.loads(out.stdout)
    return d[-1] if d and isinstance(d[0], list) else d


Q = {
    "tables": "SELECT table_name, row_count, comment FROM BORROWELL_AGENT_LAB.INFORMATION_SCHEMA.TABLES "
              "WHERE table_schema = 'DATA' AND table_type = 'BASE TABLE' ORDER BY table_name;",
    "event_mix": "SELECT event_type, COUNT(*) rows_collected, COUNT(DISTINCT client_event_id) distinct_events, "
                 "COUNT_IF(is_bot) bot_rows FROM BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS GROUP BY 1 ORDER BY 2 DESC;",
    "naive_vs_governed": """
        WITH naive AS (SELECT DATE_TRUNC(week, event_date) week,
                 COUNT_IF(event_type='offer_click') / COUNT_IF(event_type='offer_impression') naive_ctr
               FROM BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS GROUP BY 1),
             gov AS (SELECT * FROM SEMANTIC_VIEW(PRODUCT_INSIGHTS_SV
                 DIMENSIONS DATE_TRUNC('week', events.event_date) AS week METRICS events.ctr))
        SELECT n.week::DATE::VARCHAR week, ROUND(n.naive_ctr * 100, 2) naive_ctr_pct, ROUND(g.ctr * 100, 2) governed_ctr_pct
        FROM naive n JOIN gov g ON g.week = n.week ORDER BY 1;""",
    "issue_breakdown": """
        SELECT 'Raw rows' AS step, COUNT_IF(event_type='offer_click') clicks, COUNT_IF(event_type='offer_impression') impressions
          FROM BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS
        UNION ALL SELECT 'minus bots', COUNT_IF(event_type='offer_click'), COUNT_IF(event_type='offer_impression')
          FROM BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS WHERE NOT is_bot
        UNION ALL SELECT 'minus test accounts', COUNT_IF(event_type='offer_click'), COUNT_IF(event_type='offer_impression')
          FROM BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS e JOIN MEMBERS_V m USING (member_id) WHERE NOT is_bot
        UNION ALL SELECT 'minus duplicate client events', COUNT_IF(event_type='offer_click'), COUNT_IF(event_type='offer_impression')
          FROM OFFER_EVENTS_V;""",
    "search": "SELECT r.value:title::VARCHAR title, r.value:doc_type::VARCHAR doc_type FROM TABLE(FLATTEN(PARSE_JSON("
              f"SNOWFLAKE.CORTEX.SEARCH_PREVIEW('{S}.EXPERIMENT_DOCS_SEARCH', "
              "'{\"query\": \"why did CTR drop in late September\", \"columns\": [\"title\", \"doc_type\"], \"limit\": 3}'))"
              ":results)) r;",
    "readout": "SELECT * FROM SEMANTIC_VIEW(PRODUCT_INSIGHTS_SV DIMENSIONS exp114.arm METRICS exp114.exp_assigned_members, "
               "exp114.exp_exposed_members, exp114.exp_ctr, exp114.exp_approval_rate, exp114.exp_referral_revenue, "
               "exp114.exp_revenue_per_exposed_member) ORDER BY arm;",
    "recommend_42": "SELECT * FROM TABLE(RECOMMEND_OFFERS(42, 3));",
    "member_42": "SELECT member_id, province, score_band, is_newcomer FROM MEMBERS_V WHERE member_id = 42;",
    "payout_rank_42": """SELECT r.rnk, o.offer_name, o.partner_name, o.payout_cad
        FROM BORROWELL_AGENT_LAB.DATA.OFFER_RANKINGS r JOIN OFFERS_V o USING (offer_id)
        JOIN MEMBERS_V m ON m.score_band_idx = r.score_band_idx
        WHERE m.member_id = 42 AND r.policy = 'payout_ranked' AND r.rnk <= 3 ORDER BY r.rnk;""",
    "policy_comparison": "SELECT * FROM RANKING_POLICY_COMPARISON ORDER BY expected_revenue_per_application_cad DESC;",
    "dup_impressions": """SELECT platform, app_version, surface, (event_date >= '2026-09-21')::VARCHAR after_sep21,
        COUNT(*) rows_collected, COUNT(DISTINCT client_event_id) distinct_events
        FROM BORROWELL_AGENT_LAB.DATA.TELEMETRY_EVENTS WHERE event_type = 'offer_impression'
        GROUP BY ALL HAVING rows_collected <> distinct_events ORDER BY 1, 2, 3, 4;""",
    "views": f"SELECT table_name view_name, (SELECT COUNT(*) FROM {S}.OFFER_EVENTS_V) offer_events_v_rows "
             f"FROM BORROWELL_AGENT_LAB.INFORMATION_SCHEMA.VIEWS WHERE table_schema = 'LAB_{N}' ORDER BY 1;",
    "objects": f"SHOW OBJECTS IN SCHEMA {S};",
    "agents": f"SHOW AGENTS IN SCHEMA {S};",
    "mcp": f"SHOW MCP SERVERS IN SCHEMA {S};",
}
res = {}
for k, q in Q.items():
    try:
        res[k] = sql(q)
    except subprocess.CalledProcessError as e:
        res[k] = [{"ERROR": (e.stderr or e.stdout)[-400:]}]
    print(k, len(res[k]))
Path("captured").mkdir(exist_ok=True)
Path("captured/results.json").write_text(json.dumps(res, indent=1, default=str))
