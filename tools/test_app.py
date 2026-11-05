"""Headless smoke test: render every page with AppTest in both modes and fail on any exception.
Interactive mode must show no dry-run panels; dry-run mode must show every panel in dry_run.PANELS.
Run: python tools/test_app.py   (from the repo root)"""
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import dry_run  # noqa: E402

pages = sorted((ROOT / "app_pages").glob("*.py"))
failed = 0
panels_seen = 0
for mode in ("interactive", "dry-run"):
    print(f"--- {mode}")
    for p in pages:
        at = AppTest.from_file(str(p), default_timeout=30)
        at.session_state["lab_name"] = "ARCHANA" if mode == "interactive" else "DEMO"
        at.session_state["_dry_run"] = mode == "dry-run"
        at.run()
        errs = [e.value for e in at.exception]
        code_blocks = "\n".join(c.value for c in at.code)
        leftover = [t for t in ("{SCHEMA}", "{ROLE}", "{FQ_SCHEMA}", "{NAME}") if t in code_blocks]
        md = "\n".join(m.value for m in at.markdown)
        panels = md.count(":material/fact_check:")
        bad_mode = (mode == "interactive" and panels) or "No capture" in md
        panels_seen += panels if mode == "dry-run" else 0
        ok = not errs and not leftover and not bad_mode
        failed += not ok
        print(f"{'OK ' if ok else 'ERR'} {p.name:24s} code={len(at.code):2d} panels={panels} "
              f"refs={'y' if 'References' in md else 'n'} "
              f"{'unfilled=' + str(leftover) if leftover else ''} {errs[0][:300] if errs else ''}")
want = len(dry_run.PANELS)
print(f"dry-run panels rendered: {panels_seen} (registry has {want})")
failed += panels_seen < want
sys.exit(1 if failed else 0)
