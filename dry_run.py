"""Dry-run mode: show captured results from a real run of the lab under each step.

The interactive guide calls `show(key)` after each step; it renders nothing unless the app was started from
Dry_Run_Results.py. Results come from captured/ (tools/capture.py for SQL, tools/agent_eval.py for the agent).
"""
import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

_DIR = Path(__file__).resolve().parent / "captured"
CAPTURED_ON = "3-5 Nov 2026"
RUN_AS = "BORROWELL_AGENT_LAB.LAB_DEMO (role PI_LAB_DEMO)"


def enabled() -> bool:
    return bool(st.session_state.get("_dry_run"))


@st.cache_data
def _load(name: str):
    p = _DIR / name
    return json.loads(p.read_text()) if p.exists() else None


def _results() -> dict:
    return _load("results.json") or {}


def _eval() -> dict:
    return {e["id"]: e for e in (_load("eval_after_fix.json") or [])}


def _md(text: str) -> str:
    return re.sub(r"(?<!\\)\$", r"\\$", text)


def _df(key: str, cols: dict | None = None) -> pd.DataFrame:
    df = pd.DataFrame(_results().get(key, []))
    for c in df.columns:  # snow sql --format json returns NUMBER(p,s) as strings
        if not pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c]):
            num = pd.to_numeric(df[c], errors="coerce")
            if num.notna().all():
                df[c] = num
    if cols:
        df = df[[c for c in cols if c in df.columns]].rename(columns=cols)
    return df


def _table(df: pd.DataFrame, **kw):
    st.dataframe(df, hide_index=True, width="stretch", **kw)


def _clean_answer(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text or "").strip()


def _before_fix_answer() -> tuple[str, str]:
    """The agent's EXP-114 readout before the Session 5 fix (raw DATA_AGENT_RUN response)."""
    raw = _load("raw_e1_before_fix.json") or []
    try:
        row = raw[2][0]
        resp = next(iter(row.values()))
        resp = json.loads(resp) if isinstance(resp, str) else resp
    except (IndexError, StopIteration, TypeError, ValueError):
        return "", ""
    text, sql = [], ""
    for c in resp.get("content", []):
        if c.get("type") == "text":
            text.append(c["text"])
        elif c.get("type") == "tool_result" and not sql:
            for cc in c["tool_result"].get("content", []):
                sql = cc.get("json", {}).get("sql", "") or sql
    return _clean_answer("\n\n".join(text)), sql


def _agent_answer(eid: str, title: str, show_sql: bool = True):
    e = _eval().get(eid)
    if not e:
        st.caption(f"No capture for {eid}.")
        return
    st.markdown(f"**{title}**")
    st.markdown(f"> {_md(e['question'])}")
    with st.container(border=True):
        st.markdown(_md(_clean_answer(e["answer"])))
    tools = " → ".join(f"`{t}`" for t in e["tools"]) or "none (answered from instructions)"
    st.caption(f"Tools called: {tools}")
    if show_sql and e.get("sql"):
        with st.expander(":material/code: SQL the agent generated"):
            for s in e["sql"]:
                st.code(s, language="sql")


# ── one renderer per step ────────────────────────────────────────────────────
def _s1_tables():
    _table(_df("tables", {"TABLE_NAME": "Table", "ROW_COUNT": "Rows", "COMMENT": "Comment"}))


def _s1_profile():
    _table(_df("event_mix", {"EVENT_TYPE": "Event type", "ROWS_COLLECTED": "Rows", "DISTINCT_EVENTS":
                             "Distinct client_event_id", "BOT_ROWS": "Bot rows"}))
    df = _df("naive_vs_governed", {"WEEK": "Week", "NAIVE_CTR_PCT": "Naive CTR %"})
    st.markdown("**Naive weekly CTR on raw rows** - note the step down from the week of 21 Sep")
    st.line_chart(df.set_index("Week"), height=220)


def _s1_dups():
    _table(_df("dup_impressions", {"PLATFORM": "Platform", "APP_VERSION": "App version", "SURFACE": "Surface",
                                   "AFTER_SEP21": "On/after 21 Sep", "ROWS_COLLECTED": "Rows",
                                   "DISTINCT_EVENTS": "Distinct events"}))
    st.caption("Only one combination has more rows than distinct events - exactly 2x, so every impression "
               "is sent twice. Most of them land after 21 Sep, when 5.2.0 rolled out widely.")


def _s2_views():
    df = _df("views", {"VIEW_NAME": "View"})
    st.markdown("**Views in `LAB_DEMO` at the end of the run**")
    _table(df)
    rows = (_results().get("views") or [{}])[0].get("OFFER_EVENTS_V_ROWS")
    if rows:
        st.metric("OFFER_EVENTS_V rows (all four event types, deduplicated)", f"{rows:,}")
    st.caption("`EXP114_MEMBER_OUTCOMES_V` is added in Session 5 and `RANKING_POLICY_COMPARISON` in the stretch; "
               "after Session 2 you have the first four.")


def _s2_prove():
    df = _df("naive_vs_governed", {"WEEK": "Week", "NAIVE_CTR_PCT": "Naive CTR %",
                                   "GOVERNED_CTR_PCT": "Governed CTR % (semantic view)"})
    st.line_chart(df.set_index("Week"), height=260)
    with st.expander(":material/table: Weekly values"):
        _table(df)
    st.markdown("**Where the naive numbers go wrong** - offer clicks and impressions after each fix")
    _table(_df("issue_breakdown", {"STEP": "Step", "CLICKS": "Clicks", "IMPRESSIONS": "Impressions"}))


def _s3_search():
    st.markdown("> why did CTR drop in late September")
    _table(_df("search", {"TITLE": "Result (ranked)", "DOC_TYPE": "Doc type"}))


def _s4_create():
    _table(_df("agents", {"name": "Agent", "schema_name": "Schema", "comment": "Comment"}))
    objs = _df("objects", {"name": "Object", "kind": "Kind"})
    st.caption("Objects in the schema at the end of the run: " + ", ".join(f"`{n}`" for n in objs.get("Object", [])))


def _s4_ask():
    t1, t2 = st.tabs(["Priya: EXP-114 readout", "Marco: the September CTR drop"])
    with t1:
        text, sql = _before_fix_answer()
        st.markdown("> Read out EXP-114: did the payout-ranked carousel win? "
                    "Include revenue per exposed member for both arms.")
        with st.container(border=True):
            st.markdown(_md(text) if text else "_No capture._")
        st.error("**Spot the error.** The conclusion (it lost on the approval guardrail) is right, but "
                 "*revenue per exposed member up \\$3.54* is wrong. The real figure is **down \\$0.38** "
                 "(\\$37.30 → \\$36.92). Session 5's eval catches this.", icon=":material/bug_report:")
        if sql:
            with st.expander(":material/code: The SQL behind it - events joined to applications"):
                st.code(sql, language="sql")
    with t2:
        _agent_answer("E2", "Marco's question")


def _s5_eval_before():
    st.markdown("Before the fix, **E1 fails**: the agent's revenue per exposed member doesn't match the "
                "answer key (it's the readout from Session 4). E5 also fails until you build the stretch tool.")
    _table(pd.DataFrame([
        {"Check": "E1 EXP-114 readout", "Result": "FAIL - revenue per exposed member wrong (fan-out)"},
        {"Check": "E2 September CTR drop", "Result": "PASS"},
        {"Check": "E3 Top partner, October", "Result": "PASS"},
        {"Check": "E4 Approval rate by score band", "Result": "PASS"},
        {"Check": "E5 Offers for member 42", "Result": "FAIL - needs the stretch tool"},
        {"Check": "E6 Refuses to guarantee approval", "Result": "PASS"},
    ]))
    st.caption("Expected scorecard per this step's checkpoint. Only E1's failing answer was captured verbatim "
               "(Session 4); the full captured eval is the 6/6 run after the fix and stretch.")


def _s5_fix():
    df = _df("readout", {"ARM": "Arm", "EXP_ASSIGNED_MEMBERS": "Assigned", "EXP_EXPOSED_MEMBERS": "Exposed",
                         "EXP_CTR": "CTR", "EXP_APPROVAL_RATE": "Approval rate",
                         "EXP_REFERRAL_REVENUE": "Referral revenue (CAD)",
                         "EXP_REVENUE_PER_EXPOSED_MEMBER": "Revenue per exposed member (CAD)"})
    for c in ("CTR", "Approval rate"):
        df[c] = df[c].astype(float).map("{:.2%}".format)
    for c in ("Referral revenue (CAD)", "Revenue per exposed member (CAD)"):
        df[c] = df[c].astype(float).map("{:,.2f}".format)
    st.markdown("**Governed readout from the `exp114` semantic view table**")
    _table(df)
    rows = {r["ARM"]: r for r in _results().get("readout", [])}
    if {"control", "treatment"} <= rows.keys():
        c, t = rows["control"], rows["treatment"]
        m = st.columns(3)
        m[0].metric("CTR", f"{float(t['EXP_CTR']):.2%}", f"{(float(t['EXP_CTR']) - float(c['EXP_CTR'])) * 100:+.2f} pts")
        m[1].metric("Approval rate", f"{float(t['EXP_APPROVAL_RATE']):.2%}",
                    f"{(float(t['EXP_APPROVAL_RATE']) - float(c['EXP_APPROVAL_RATE'])) * 100:+.1f} pts")
        rp_t, rp_c = float(t["EXP_REVENUE_PER_EXPOSED_MEMBER"]), float(c["EXP_REVENUE_PER_EXPOSED_MEMBER"])
        m[2].metric("Revenue per exposed member", f"${rp_t:.2f}", f"{rp_t - rp_c:+.2f} CAD")
        st.caption("Treatment vs control. Higher CTR, much lower approval rate, slightly less revenue.")
    _agent_answer("E1", "The agent's answer after the fix")


def _s5_eval_after():
    rows = [{"Check": k, "Question": e["question"], "Expected": e["expected"],
             "Result": "PASS" if e["passed"] else "FAIL"} for k, e in _eval().items()]
    st.markdown(f"**Final eval: {sum(r['Result'] == 'PASS' for r in rows)}/{len(rows)}** "
                "(with the stretch tool in place)")
    _table(pd.DataFrame(rows))
    with st.expander(":material/forum: All six answers"):
        for k in _eval():
            _agent_answer(k, k, show_sql=False)
            st.divider()


def _s5_mcp():
    _table(_df("mcp", {"name": "MCP server", "schema_name": "Schema", "comment": "Comment"}))


def _st_ranking():
    m = (_results().get("member_42") or [{}])[0]
    st.markdown(f"**Member 42** - {m.get('PROVINCE', '?')}, score band **{m.get('SCORE_BAND', '?')}**, "
                f"newcomer: {m.get('IS_NEWCOMER', '?')}")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Payout ranking (EXP-114 treatment)**")
        _table(_df("payout_rank_42", {"RNK": "#", "OFFER_NAME": "Offer", "PARTNER_NAME": "Partner",
                                      "PAYOUT_CAD": "Payout (CAD)"}))
    with c2:
        st.markdown("**`RECOMMEND_OFFERS(42, 3)` - approval-aware**")
        df = _df("recommend_42", {"RNK": "#", "OFFER_NAME": "Offer", "APPROVAL_ODDS": "Approval odds",
                                  "PAYOUT_CAD": "Payout", "EXPECTED_REVENUE_CAD": "Expected revenue"})
        if "Approval odds" in df:
            df["Approval odds"] = df["Approval odds"].astype(float).map("{:.0%}".format)
        _table(df)


def _st_policy():
    df = _df("policy_comparison", {"POLICY": "Policy",
                                   "EXPECTED_REVENUE_PER_APPLICATION_CAD": "Expected revenue per application (CAD)",
                                   "AVG_APPROVAL_ODDS": "Avg approval odds"})
    _table(df)
    if not df.empty:
        chart = df.set_index("Policy")[["Expected revenue per application (CAD)"]].astype(float)
        st.bar_chart(chart, horizontal=True, height=200)


def _st_tool():
    _agent_answer("E5", "Question E5")
    _agent_answer("E6", "Guardrail check E6", show_sql=False)


PANELS = {
    "s1_tables": _s1_tables, "s1_profile": _s1_profile, "s1_dups": _s1_dups,
    "s2_views": _s2_views, "s2_prove": _s2_prove,
    "s3_search": _s3_search,
    "s4_create": _s4_create, "s4_ask": _s4_ask,
    "s5_eval_before": _s5_eval_before, "s5_fix": _s5_fix, "s5_eval_after": _s5_eval_after, "s5_mcp": _s5_mcp,
    "st_ranking": _st_ranking, "st_policy": _st_policy, "st_tool": _st_tool,
}


RESPONSE_PANELS = {"s4_ask", "s5_fix", "st_tool", "s5_eval_after"}  # agent answers, not just SQL

# Which captured panels answer each prompt. Prompt 2.2 (create the semantic view) has no captured output.
PROMPT_PANELS = {
    "Prompt 1.1": ["s1_tables"], "Prompt 1.2": ["s1_profile"], "Prompt 1.3": ["s1_dups"],
    "Prompt 2.1": ["s2_views"], "Prompt 2.3": ["s2_prove"],
    "Prompt 3.1": ["s3_search"],
    "Prompt 4.1": ["s4_create"], "Prompt 4.2": ["s4_ask"],
    "Prompt 5.1": ["s5_eval_before"], "Prompt 5.2": ["s5_fix"], "Prompt 5.3": ["s5_mcp"],
    "Prompt S.1": ["st_ranking"], "Prompt S.2": ["st_policy"], "Prompt S.3": ["st_tool", "s5_eval_after"],
}
PANEL_TITLES = {"s5_eval_after": "Simulated response: the final eval"}


def _state_key(prompt_id: str) -> str:
    return "_coco_" + prompt_id.replace(" ", "_").replace(".", "_")


def _flip(prompt_id: str):
    k = _state_key(prompt_id)
    st.session_state[k] = not st.session_state.get(k, False)


def response_button(prompt_id: str) -> bool:
    """CoCo Response toggle for a prompt header. Returns False (draw nothing) if there's no capture."""
    if not enabled() or prompt_id not in PROMPT_PANELS:
        return False
    shown = st.session_state.get(_state_key(prompt_id), False)
    st.button("Hide response" if shown else "CoCo Response", key=f"btn{_state_key(prompt_id)}",
              icon=":material/visibility_off:" if shown else ":material/smart_toy:",
              type="secondary" if shown else "primary", on_click=_flip, args=(prompt_id,), width="stretch")
    return True


def prompt_response(prompt_id: str):
    """Render the captured result(s) for a prompt when its CoCo Response button is on."""
    if enabled() and st.session_state.get(_state_key(prompt_id), False):
        for key in PROMPT_PANELS.get(prompt_id, []):
            show(key, PANEL_TITLES.get(key))


def show(key: str, title: str | None = None):
    """Render the captured result for one step. No-op in the interactive guide."""
    if not enabled():
        return
    with st.container(border=True):
        title = title or ("Simulated response" if key in RESPONSE_PANELS else "Simulated result set")
        st.markdown(f"##### :material/fact_check: {title}")
        st.caption(f"Captured from a real run as `{RUN_AS}`, {CAPTURED_ON}. Synthetic data.")
        PANELS[key]()


def banner():
    if enabled():
        st.info("**Simulated results (read-only).** You don't need a Snowflake connection. Click **CoCo Response** "
                "next to a prompt to see the result it produced on a real run of this lab, so you can follow along or catch up. "
                "Prompts and SQL use the `DEMO` lab.", icon=":material/visibility:")
