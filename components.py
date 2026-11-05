import re
import streamlit as st
from pathlib import Path

LAB_DB = "BORROWELL_AGENT_LAB"
_HERE = Path(__file__).resolve().parent
SQL_DIR = _HERE / "sql" if (_HERE / "sql").is_dir() else _HERE.parent / "sql"


@st.cache_data(max_entries=50)
def sql_file(rel_path: str) -> str:
    """Admin scripts are shown straight from ../sql so the guide never drifts from the tested SQL."""
    p = SQL_DIR / rel_path
    return p.read_text() if p.exists() else f"-- {rel_path} not found next to the app (expected {p})"


def render_sql_file(rel_path: str, label: str | None = None, expanded: bool = False):
    with st.expander(label or f":material/description: `{rel_path}`", expanded=expanded):
        st.code(sql_file(rel_path), language="sql", line_numbers=True)


DOC_DIR = SQL_DIR.parent


@st.cache_data(max_entries=20)
def doc_file(name: str) -> str:
    """Hand-out docs (questionnaire, attendee prep) live next to sql/ and are shown as-is."""
    p = DOC_DIR / name
    return p.read_text() if p.exists() else f"{name} not found next to the app (expected {p})"


def render_doc_download(name: str, label: str, mime: str = "text/markdown"):
    st.download_button(label, data=doc_file(name), file_name=name, mime=mime,
                       icon=":material/download:", key=f"dl_{name}")

# Prompt ids per lab section - drive the green tick next to each page title in the sidebar.
SESSION_PROMPTS = {
    1: ["Prompt 1.1", "Prompt 1.2", "Prompt 1.3"],
    2: ["Prompt 2.1", "Prompt 2.2", "Prompt 2.3"],
    3: ["Prompt 3.1"],
    4: ["Prompt 4.1", "Prompt 4.2"],
    5: ["Prompt 5.1", "Prompt 5.2", "Prompt 5.3"],
    "S": ["Prompt S.1", "Prompt S.2", "Prompt S.3"],
}


# ── attendee context ─────────────────────────────────────────────────────────
def lab_name() -> str:
    raw = st.session_state.get("lab_name") or "DEMO"
    clean = "".join(c for c in raw.upper() if c.isalnum() or c == "_")
    return clean or "DEMO"


def ctx() -> dict:
    name = lab_name()
    return {
        "NAME": name,
        "SCHEMA": f"LAB_{name}",
        "FQ_SCHEMA": f"{LAB_DB}.LAB_{name}",
        "ROLE": f"PI_LAB_{name}",
        "DB": LAB_DB,
        "WH": "PI_LAB_WH",
    }


def _md(text: str) -> str:
    """Streamlit markdown reads $...$ as LaTeX; escape dollar amounts in prose (code blocks use st.code)."""
    return re.sub(r"(?<!\\)\$", r"\\$", text)


def fill(text: str) -> str:
    """Replace {SCHEMA}, {ROLE}, ... placeholders with the attendee's lab values."""
    out = text
    for k, v in ctx().items():
        out = out.replace("{" + k + "}", v)
    return out


# ── completion tracking ──────────────────────────────────────────────────────
def _done_store() -> dict:
    if "_done" not in st.session_state:
        st.session_state["_done"] = {}
    return st.session_state["_done"]


def _prompt_key(prompt_id: str) -> str:
    return prompt_id.replace(" ", "_").replace(".", "_")


def _on_toggle(prompt_id: str):
    key = _prompt_key(prompt_id)
    _done_store()[key] = st.session_state[f"_cb_{key}"]


def is_session_complete(session_id) -> bool:
    prompts = SESSION_PROMPTS.get(session_id, [])
    store = _done_store()
    return len(prompts) > 0 and all(store.get(_prompt_key(p), False) for p in prompts)


# ── building blocks ──────────────────────────────────────────────────────────
def render_session_header(label: str, title: str, duration: str, building: str):
    st.title(f"{label}: {title}")
    col1, col2 = st.columns(2)
    col1.markdown(f":material/schedule: **{duration}**")
    col2.markdown(f":material/construction: **Building**: {building}")
    st.space("small")


def render_execution_context():
    import dry_run

    dry_run.banner()
    st.info(
        ":material/terminal: **Primary: CoCo Desktop or CoCo CLI** - paste each prompt into CoCo.  "
        ":material/web: **Also possible in Snowsight** - open *Do it in Snowsight* under any step.",
        icon=None,
    )
    render_role_callout()


def render_role_callout(when: str = "Before you paste any prompt on this page"):
    """The lab never changes users' DEFAULT_ROLE, so every page reminds attendees to switch role themselves."""
    c = ctx()
    with st.container(border=True):
        st.warning(f"**Set your role.** {when}, check CoCo (or your worksheet) is using role "
                   f"**`{c['ROLE']}`** and warehouse **`PI_LAB_WH`**. Unless your admin set it as your default, "
                   "a new CoCo session, reconnect or new worksheet starts in your usual role.",
                   icon=":material/badge:")
        st.code(f"USE ROLE {c['ROLE']};\nUSE SECONDARY ROLES NONE;\nUSE WAREHOUSE PI_LAB_WH;\n"
                "SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE();", language="sql")
        st.caption(f"In CoCo you can also just ask: *\"use role {c['ROLE']} and warehouse PI_LAB_WH\"*.")


def render_what_why(what: str, why: str):
    c1, c2 = st.columns(2)
    with c1.container(border=True, height="stretch"):
        st.markdown("##### :material/flag: What")
        st.markdown(_md(what))
    with c2.container(border=True, height="stretch"):
        st.markdown("##### :material/lightbulb: Why it matters for Borrowell")
        st.markdown(_md(why))


def render_prompt(prompt_id: str, title: str, prompt_text: str):
    key = _prompt_key(prompt_id)
    cb_key = f"_cb_{key}"
    store = _done_store()
    if cb_key not in st.session_state:
        st.session_state[cb_key] = store.get(key, False)
    with st.container(border=True):
        header_col, check_col = st.columns([4, 1], vertical_alignment="center")
        with header_col:
            st.markdown(f"#### :material/terminal: {prompt_id} - {title}")
        with check_col:
            import dry_run

            if not dry_run.enabled():
                st.checkbox("Done", key=cb_key, on_change=_on_toggle, args=(prompt_id,))
            else:
                dry_run.response_button(prompt_id)
        st.caption("Copy this prompt into CoCo Desktop or the CoCo CLI")
        st.code(fill(prompt_text), language="text", wrap_lines=True)
        dry_run.prompt_response(prompt_id)


def render_explanation(title: str, body: str):
    with st.expander(f":material/school: {title}", expanded=False):
        st.markdown(_md(fill(body)))


def render_snowsight_route(steps: list[str], sql: str | None = None):
    """The same step done in the Snowsight UI (and/or a worksheet)."""
    with st.expander(":material/web: Do it in Snowsight", expanded=False):
        for i, s in enumerate(steps, 1):
            st.markdown(f"{i}. {fill(s)}")
        if sql:
            st.caption("Or paste into a Snowsight worksheet:")
            st.code(fill(sql), language="sql")


def render_checkpoint(text: str, sql: str | None = None):
    with st.container(border=True):
        st.markdown(_md(f":material/task_alt: **Checkpoint** - {fill(text)}"))
        if sql:
            st.code(fill(sql), language="sql")


def render_fallback(sql: str):
    with st.expander(":material/sos: Behind? Run this to catch up", expanded=False):
        st.caption("Exactly what CoCo should have produced. Run it as your lab role.")
        st.code(fill(sql), language="sql")


def render_technologies_used(technologies: list[dict]):
    st.markdown("##### :material/build: Snowflake capabilities in this section")
    cols = st.columns(min(len(technologies), 3))
    for i, tech in enumerate(technologies):
        with cols[i % len(cols)].container(border=True, height="stretch"):
            st.markdown(f":material/{tech.get('icon', 'widgets')}: **{tech['name']}**")
            st.caption(_md(tech["description"]))


def render_key_concepts(concepts: list[dict]):
    st.markdown("##### :material/lightbulb: Key concepts")
    for concept in concepts:
        with st.expander(f"**{concept['term']}**"):
            st.markdown(_md(concept["definition"]))


def render_what_you_built(items: list[str]):
    st.markdown("##### :material/check_circle: What you built")
    for item in items:
        st.markdown(_md(f"- :green-badge[Done] {fill(item)}"))


# ── page footers (required on every lab page) ────────────────────────────────
def render_real_world_examples(items: list[dict]):
    st.divider()
    st.markdown("##### :material/apartment: Where Borrowell would use this")
    cols = st.columns(2)
    for i, it in enumerate(items):
        with cols[i % 2].container(border=True, height="stretch"):
            st.markdown(f"**{it['title']}**")
            st.markdown(_md(it["body"]))


def render_references(links: dict):
    """links = {"Quickstarts": [(title, url, note)], "Docs": [...], "Blogs and guidance": [...]}"""
    from content.links import VERIFIED_ON

    st.markdown("##### :material/menu_book: References")
    for group, items in links.items():
        if not items:
            continue
        st.markdown(f"**{group}**")
        for title, url, note in items:
            suffix = f" - {note}" if note else ""
            st.markdown(f"- [{title}]({url}){suffix}")
    st.caption(f"Links verified {VERIFIED_ON}.")


def answer_key(start: str, end: str | None = None) -> str:
    """One section of sql/answer_key.sql (from the line containing `start` up to `end`), pointed at the
    attendee's schema and role - the tested SQL, never retyped."""
    import re

    text = sql_file("answer_key.sql")
    i = text.find(start)
    if i < 0:
        return f"-- '{start}' not found in sql/answer_key.sql"
    i = text.index("\n", i) + 1
    j = text.find(end, i) if end else -1
    body = text[i:j if j > 0 else len(text)]
    body = re.sub(r"^-- =+\n", "", body, flags=re.M).strip()
    body = (body.replace("BORROWELL_AGENT_LAB.LAB_DEMO", "{FQ_SCHEMA}").replace("PI_LAB_DEMO", "{ROLE}")
                .replace("LAB_DEMO", "{SCHEMA}"))
    return "USE ROLE {ROLE};\nUSE SECONDARY ROLES NONE;\nUSE WAREHOUSE {WH};\nUSE SCHEMA {FQ_SCHEMA};\n\n" + body
