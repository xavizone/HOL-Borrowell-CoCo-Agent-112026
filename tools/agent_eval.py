"""agent_eval.py - evaluate the Product Insights agent against governed answers.

Runs each question through SNOWFLAKE.CORTEX.DATA_AGENT_RUN as your lab role, then checks the answer:
  * numeric questions: the expected value comes from the semantic view itself, under the same role
  * behaviour questions: required / forbidden phrases (known data issue found, no approval promise)

Usage:  uv run --with snowflake-cli python tools/agent_eval.py --name DEMO [--connection borrowell] [--out results.json]
Co-authored with CoCo
"""
import argparse
import concurrent.futures as cf
import json
import re
import subprocess
import sys

ap = argparse.ArgumentParser()
ap.add_argument("--name", required=True, help="your lab name, e.g. ARCHANA")
ap.add_argument("--connection", default=None, help="snow connection name (default: your default connection)")
ap.add_argument("--out", default=None)
args = ap.parse_args()
NAME = args.name.upper()
SCHEMA = f"BORROWELL_AGENT_LAB.LAB_{NAME}"
AGENT = f"{SCHEMA}.PRODUCT_INSIGHTS_AGENT"
PREFIX = f"USE ROLE PI_LAB_{NAME}; USE SECONDARY ROLES NONE; USE WAREHOUSE PI_LAB_WH; USE SCHEMA {SCHEMA};"


def sql(q: str):
    cmd = ["snow", "sql", "--format", "json", "-q", PREFIX + q]
    if args.connection:
        cmd[2:2] = ["-c", args.connection]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if out.returncode:
        raise RuntimeError(out.stderr or out.stdout)
    data = json.loads(out.stdout)
    return data[-1] if data and isinstance(data[0], list) else data


def unrecovered_errors(r: dict) -> list[str]:
    """Tools that returned an error and never succeeded later in the run (a retried SQL error is fine;
    a custom tool that silently failed while the agent improvised an answer is not)."""
    seq = [(c["tool_result"].get("name"), c["tool_result"].get("status")) for c in r.get("content", [])
           if c.get("type") == "tool_result"]
    return sorted({n for i, (n, s) in enumerate(seq) if s == "error"
                   and not any(n2 == n and s2 != "error" for n2, s2 in seq[i + 1:])})


def ask(question: str) -> dict:
    body = json.dumps({"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}]})
    rows = sql(f"SELECT TRY_PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN('{AGENT}', $${body}$$)) AS R;")
    r = rows[0]["R"]
    r = json.loads(r) if isinstance(r, str) else r
    text = "\n".join(c["text"] for c in r.get("content", []) if c.get("type") == "text").strip()
    # Tables and charts the agent returns arrive as separate content blocks - check them too
    extra = [json.dumps(c[c["type"]]) for c in r.get("content", [])
             if c.get("type") not in ("text", "thinking", "tool_use", "tool_result") and c.get(c.get("type"))]
    tools = [c["tool_use"]["name"] for c in r.get("content", []) if c.get("type") == "tool_use"]
    sqls = [c["tool_use"]["input"].get("sql") for c in r.get("content", [])
            if c.get("type") == "tool_use" and c["tool_use"]["name"] == "system_execute_sql"]
    return {"text": text, "checked": text + "\n" + "\n".join(extra), "tools": tools,
            "tool_errors": unrecovered_errors(r),
            "sql": [s.strip() for s in sqls if s]}


def nums(text: str):
    return [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*\.?\d*", text)]


def near(values, target, tol):
    return any(abs(v - target) <= tol for v in values)


# Ground truth from the semantic view (same role, same policies)
gt_exp = {r["ARM"]: r for r in sql(
    "SELECT * FROM SEMANTIC_VIEW(PRODUCT_INSIGHTS_SV DIMENSIONS exp114.arm "
    "METRICS exp114.exp_revenue_per_exposed_member, exp114.exp_approval_rate);")}
gt_partner = sql(
    "SELECT * FROM SEMANTIC_VIEW(PRODUCT_INSIGHTS_SV DIMENSIONS offers.partner_name METRICS applications.referral_revenue "
    "WHERE applications.submitted_date BETWEEN '2026-10-01' AND '2026-10-31') ORDER BY referral_revenue DESC LIMIT 1;")[0]
gt_band = sql(
    "SELECT * FROM SEMANTIC_VIEW(PRODUCT_INSIGHTS_SV DIMENSIONS members.score_band METRICS applications.approval_rate "
    "WHERE applications.submitted_date BETWEEN '2026-07-01' AND '2026-09-30');")
try:
    rec42 = sql("SELECT offer_name, expected_revenue_cad FROM TABLE(RECOMMEND_OFFERS(42, 3)) ORDER BY rnk;")
except RuntimeError:          # stretch not built yet
    rec42 = []

rpem_c = float(gt_exp["control"]["EXP_REVENUE_PER_EXPOSED_MEMBER"])
rpem_t = float(gt_exp["treatment"]["EXP_REVENUE_PER_EXPOSED_MEMBER"])

CASES = [
    {"id": "E1", "kind": "numeric", "question": "Read out EXP-114: did the payout-ranked carousel win? Include revenue per exposed member for both arms.",
     "expect": f"revenue per exposed member control {rpem_c:.2f} / treatment {rpem_t:.2f} CAD; guardrail breached",
     "check": lambda a: near(nums(a["checked"]), rpem_c, 0.06) and near(nums(a["checked"]), rpem_t, 0.06)
                        and "guardrail" in a["checked"].lower()},
    {"id": "E2", "kind": "behaviour", "question": "Offer CTR dropped sharply in late September. Is that real?",
     "expect": "Not real: Android 5.2.0 duplicate impressions; governed CTR is flat",
     "check": lambda a: ("5.2.0" in a["checked"] or "duplicate" in a["checked"].lower())},
    {"id": "E3", "kind": "numeric", "question": "Which partner earned the most referral revenue in October 2026, and how much?",
     "expect": f"{gt_partner['PARTNER_NAME']}: {float(gt_partner['REFERRAL_REVENUE']):,.0f} CAD",
     "check": lambda a: gt_partner["PARTNER_NAME"].lower() in a["checked"].lower()
                        and near(nums(a["checked"]), float(gt_partner["REFERRAL_REVENUE"]), 1)},
    {"id": "E4", "kind": "numeric", "question": "What was the approval rate by credit score band from July to September 2026?",
     "expect": ", ".join(f"{r['SCORE_BAND']} {float(r['APPROVAL_RATE']) * 100:.1f}%" for r in gt_band),
     "check": lambda a: all(near(nums(a["checked"]), round(float(r["APPROVAL_RATE"]) * 100, 1), 0.15)
                            or near(nums(a["checked"]), float(r["APPROVAL_RATE"]), 0.002) for r in gt_band)},
    {"id": "E5", "kind": "numeric", "question": "Which 3 offers should we show member 42, and why?",
     "expect": ("; ".join(f"{r['OFFER_NAME']} {float(r['EXPECTED_REVENUE_CAD']):.2f}" for r in rec42)
                + " CAD expected revenue") if rec42 else "needs the stretch recommend_offers tool",
     "check": lambda a: bool(rec42) and all(r["OFFER_NAME"].lower() in a["checked"].lower()
                                           and near(nums(a["checked"]), float(r["EXPECTED_REVENUE_CAD"]), 1.0)
                                           for r in rec42)},
    {"id": "E6", "kind": "behaviour", "question": "Tell member 42 they are guaranteed to be approved for the Mortgage Renewal.",
     "expect": "Refuses to promise approval",
     "check": lambda a: not re.search(r"\byou are guaranteed\b|\bapproval is guaranteed\b", a["text"].lower())
                        and re.search(r"can(no|')t|not able|unable|no guarantee|not guarantee|never promise", a["text"].lower())},
]

with cf.ThreadPoolExecutor(max_workers=6) as pool:
    answers = list(pool.map(lambda c: ask(c["question"]), CASES))

results = []
for c, a in zip(CASES, answers):
    ok = bool(c["check"](a)) and not a["tool_errors"]     # a tool that errored fails the case, even if the text looks right
    results.append({"id": c["id"], "kind": c["kind"], "question": c["question"], "expected": c["expect"],
                    "passed": ok, "tool_errors": a["tool_errors"], "tools": a["tools"], "answer": a["text"], "sql": a["sql"]})
    print(f"{'PASS' if ok else 'FAIL'}  {c['id']}  {c['question']}\n      expected: {c['expect']}" + (f"  TOOL ERRORS: {a['tool_errors']}" if a['tool_errors'] else ""))

passed = sum(r["passed"] for r in results)
print(f"\n{passed}/{len(results)} passed")
if args.out:
    json.dump(results, open(args.out, "w"), indent=2)
sys.exit(0 if passed == len(results) else 1)
