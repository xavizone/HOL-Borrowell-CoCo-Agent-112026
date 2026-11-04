"""The lab's story: cast, chapters, turns and the Home timelines.
Edit the words here; the pages only decide where each piece appears."""
import streamlit as st

ARC = ["Explore", "Semantic layer", "Knowledge", "Agent", "Evaluate", "Outcome"]

CAST = [
    {"name": "Priya", "role": "Product manager, Marketplace Growth", "icon": ":material/campaign:",
     "says": "Owns the offers carousel and EXP-114. Wants a yes or no on shipping, today."},
    {"name": "Marco", "role": "Lifecycle marketing lead", "icon": ":material/mail:",
     "says": "Plans email and push campaigns off CTR. Saw CTR \"crash\" in late September and is worried."},
    {"name": "You", "role": "Product data science - building the team's agent", "icon": ":material/analytics:",
     "says": "Own the offers telemetry. Work in CoCo. Answer to Priya and Marco, and soon to Workwell."},
]

CHAPTERS = {
    1: {"previously": "It's Tuesday. Experiment EXP-114 (payout-ranked offer carousel) ended on 15 October.",
        "who": "Priya", "quote": "CTR is up on EXP-114. Can we ship it? And Marco says CTR crashed in late September - what happened?",
        "scene": "Today that's a Looker ticket and a day of SQL. You have the raw telemetry and CoCo.",
        "mission": "Profile the offers funnel and find what would make a quick answer wrong."},
    2: {"previously": "You found bots, test accounts and an app release that double-sends impressions.",
        "who": "Marco", "quote": "Which CTR is the real one? Looker, the notebook and the raw table all disagree.",
        "scene": "Before any agent touches this data, CTR, approval rate and revenue need one definition each.",
        "mission": "Build curated views and a semantic view with governed metrics - the layer Workwell is missing."},
    3: {"previously": "CTR has one definition, and it says September was fine.",
        "who": "Priya", "quote": "The experiment brief says there's a guardrail. Does anything you build know that?",
        "scene": "Half of a good readout isn't in a table: the guardrails, the definitions, the known data issues.",
        "mission": "Index the team's knowledge base with Cortex Search."},
    4: {"previously": "Numbers live in the semantic view; context lives in a search service.",
        "who": "Priya", "quote": "Read out EXP-114 for me. Did the payout-ranked carousel win?",
        "scene": "One domain agent for product, marketing and data science - the one Workwell will call.",
        "mission": "Create the Product Insights agent and ask it Priya's and Marco's questions."},
    5: {"previously": "The agent gave a confident readout and called the guardrail.",
        "who": "Priya", "quote": "I'm taking this to the growth review. Are you sure the numbers are right?",
        "scene": "Confident isn't correct. \"Inaccurate answers\" is why Workwell was paused.",
        "mission": "Evaluate the agent, find the wrong answer, fix it in the semantic layer, and hand the agent to Workwell over MCP."},
    6: {"previously": "EXP-114 won clicks and lost approvals. Borrowell earns on approvals.",
        "who": "Priya", "quote": "So what should the carousel rank by instead?",
        "scene": "Rank by what each member is likely to be approved for, weighted by what it pays.",
        "mission": "Build an approval-aware ranking, project the revenue lift, and give the agent the tool."},
}

TURNS = {
    1: {"changed": "You know why a naive CTR is about 2 points too high and why it \"dropped\" 12% in September.",
        "next": "Next: give CTR, approval rate and revenue one governed definition."},
    2: {"changed": "Governed CTR is flat at about 6% - September was a data issue, not a member issue.",
        "next": "Next: add the knowledge that lives outside the tables."},
    3: {"changed": "Experiment briefs, metric definitions and known data issues are searchable next to the data.",
        "next": "Next: put both behind one agent."},
    4: {"changed": "Priya can ask in plain language - and the agent reads the brief before it reads the numbers.",
        "next": "Next: prove the answers are right before anyone acts on them."},
    5: {"changed": "Every answer is checked against governed numbers, the bug is fixed where it lives, and Workwell can call the agent.",
        "next": "Stretch: turn the readout into a better ranking."},
    6: {"changed": "Priya has a ranking that projects more revenue per application and fewer declined members.",
        "next": "Epilogue below."},
}

TIMELINES = {
    "without": [("Mon 09:00", "Priya asks in Slack whether EXP-114 can ship"),
                ("Mon 11:00", "Looker shows CTR +9%; a ticket goes to data science for the full readout"),
                ("Tue 14:00", "Analyst finds the duplicate impressions; Marco's September \"crash\" was never real"),
                ("Wed 10:00", "Readout lands: approvals down 17 points, revenue per member down"),
                ("Wed 10:05", "Meanwhile, two campaigns were re-planned around a CTR drop that didn't happen")],
    "with": [("Mon 09:00", "Priya asks the Product Insights agent, inside Workwell"),
             ("Mon 09:01", "It reads the EXP-114 brief and its 5-point approval guardrail"),
             ("Mon 09:02", "Governed metrics: CTR +9%, approvals -17.6 pts, revenue per exposed member down"),
             ("Mon 09:02", "Marco's question: the September drop is the Android 5.2.0 duplicate-impression issue"),
             ("Mon 09:05", "Decision: don't ship; test approval-aware ranking next")],
}

EPILOGUE = ("**Epilogue.** EXP-114 doesn't ship, Marco's campaigns stay on plan, and the next experiment tests "
            "approval-aware ranking - read out by the same agent, with the same eval guarding it. Workwell now has a "
            "Snowflake sub-agent that answers product questions with governed numbers.")


# ── renderers (native Streamlit) ─────────────────────────────────────────────
def story_arc(current: int):
    labels = []
    for i, name in enumerate(ARC, 1):
        if i < current:
            labels.append(f":green-badge[:material/check: {name}]")
        elif i == current:
            labels.append(f":blue-badge[**{i}. {name}**]")
        else:
            labels.append(f":gray-badge[{i}. {name}]")
    st.markdown(" &nbsp;:material/arrow_forward:&nbsp; ".join(labels))


def chapter(n: int):
    c = CHAPTERS[n]
    with st.container(border=True):
        story_arc(n)
        st.caption(f":material/history: **Previously:** {c['previously']}")
        avatar = next(p["icon"] for p in CAST if p["name"] == c["who"])
        with st.chat_message(c["who"], avatar=avatar):
            st.markdown(f"**{c['who']}:** *\"{c['quote']}\"*")
        st.markdown(c["scene"])
        st.markdown(f":material/flag: **Your mission:** {c['mission']}")


def turn(n: int):
    t = TURNS[n]
    with st.container(border=True):
        st.markdown(f":material/auto_stories: **What changed:** {t['changed']}")
        st.caption(t["next"])


def cast():
    cols = st.columns(len(CAST))
    for col, p in zip(cols, CAST):
        with col.container(border=True, height="stretch"):
            st.markdown(f"##### {p['icon']} {p['name']}")
            st.caption(p["role"])
            st.markdown(p["says"])


def timelines():
    left, right = st.columns(2)
    for col, key, title, icon in [(left, "without", "A readout without the agent", ":material/sentiment_dissatisfied:"),
                                  (right, "with", "The same question with the agent", ":material/verified_user:")]:
        with col.container(border=True, height="stretch"):
            st.markdown(f"##### {icon} {title}")
            for when, what in TIMELINES[key]:
                st.markdown(f"`{when}` {what}")


def epilogue():
    st.success(EPILOGUE, icon=":material/celebration:")
