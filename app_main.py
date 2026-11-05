from pathlib import Path

import streamlit as st

from components import ctx, is_session_complete

_DIR = Path(__file__).parent


def _title(session_id, label: str) -> str:
    check = " :green[:material/check_circle:]" if is_session_complete(session_id) else ""
    return f"{label}{check}"



def main(dry_run: bool = False):
    """Shared by Workshop_Guide_Start.py (interactive) and Dry_Run_Results.py (captured results)."""
    st.set_page_config(
        page_title="Borrowell | Product Insights Agent hands-on lab" + (" - dry-run results" if dry_run else ""),
        page_icon=":material/insights:",
        layout="wide",
    )

    st.logo(
        str(_DIR / "static" / "snowflake_full_logo.png"),
        icon_image=str(_DIR / "static" / "snowflake_logo.png"),
    )

    st.session_state["_dry_run"] = dry_run
    if dry_run:
        st.session_state["lab_name"] = "DEMO"
    st.session_state.setdefault("lab_name", "DEMO")

    with st.sidebar:
        if dry_run:
            st.markdown(":material/visibility: **Dry-run results**  \nRead-only. No Snowflake connection needed.")
        st.text_input(
            disabled=dry_run,
            label="Your lab name",
            key="lab_name",
            help="The NAME your admin used in SETUP_ALL (usually your first name). Every prompt and SQL block updates to LAB_<NAME>.",
            max_chars=30,
        )
        st.caption(f"Your schema: `{ctx()['FQ_SCHEMA']}`  \nYour role: `{ctx()['ROLE']}`")

    page = st.navigation(
        {
            "": [
                st.Page("app_pages/home.py", title="Home", icon=":material/home:"),
                st.Page("app_pages/before_you_start.py", title="Before you start", icon=":material/event_available:"),
                st.Page("app_pages/install_coco.py", title="Install CoCo Desktop and CLI", icon=":material/download:"),
                st.Page("app_pages/getting_started.py", title="Getting started", icon=":material/rocket_launch:"),
                st.Page("app_pages/agenda.py", title="Agenda", icon=":material/calendar_today:"),
            ],
            "90-minute lab": [
                st.Page("app_pages/session_01.py", title=_title(1, "1. Explore the telemetry"), icon=":material/travel_explore:"),
                st.Page("app_pages/session_02.py", title=_title(2, "2. Build the semantic layer"), icon=":material/schema:"),
                st.Page("app_pages/session_03.py", title=_title(3, "3. Add knowledge with Search"), icon=":material/manage_search:"),
                st.Page("app_pages/session_04.py", title=_title(4, "4. Build the agent"), icon=":material/smart_toy:"),
                st.Page("app_pages/session_05.py", title=_title(5, "5. Evaluate and connect Workwell"), icon=":material/rule:"),
            ],
            "Stretch: business outcome": [
                st.Page("app_pages/stretch.py", title=_title("S", "Approval-aware offer ranking"), icon=":material/trending_up:"),
            ],
            "Reference": [
                st.Page("app_pages/availability.py", title="Azure Canada Central availability", icon=":material/public:"),
                st.Page("app_pages/reference_coco.py", title="CoCo prompt cheat sheet", icon=":material/chat:"),
                st.Page("app_pages/snowsight_map.py", title="Snowsight navigation map", icon=":material/map:"),
                st.Page("app_pages/troubleshooting.py", title="Troubleshooting", icon=":material/build:"),
                st.Page("app_pages/admin_setup.py", title="Lab setup (admin)", icon=":material/admin_panel_settings:"),
                st.Page("app_pages/admin_teardown.py", title="Lab teardown (admin)", icon=":material/delete_sweep:"),
            ],
        },
        position="sidebar",
    )

    page.run()
