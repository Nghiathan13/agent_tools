"""Persist the tabs and focus last set by agent helpers."""

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


DEBUGGING_URL = "http://127.0.0.1:9222"
state_path = Path(__file__).resolve().parents[1] / "open-tabs.json"


def list_tabs() -> list[dict]:
    with urlopen(f"{DEBUGGING_URL}/json/list", timeout=5) as response:
        return json.load(response)


def activate_tab(target_id: str) -> None:
    with urlopen(f"{DEBUGGING_URL}/json/activate/{quote(target_id, safe='')}", timeout=5):
        pass


def focused_tab_id() -> str | None:
    if not state_path.exists():
        return None
    return json.loads(state_path.read_text()).get("focusedTabId")


def snapshot_tabs(focus_id: str | None = None) -> dict:
    tabs = [
        {
            "id": tab["id"],
            "type": tab["type"],
            "title": tab.get("title", ""),
            "url": tab["url"],
        }
        for tab in list_tabs()
        if tab["type"] == "page"
    ]
    tab_ids = {tab["id"] for tab in tabs}
    focus_id = focus_id if focus_id in tab_ids else focused_tab_id()
    if focus_id not in tab_ids:
        focus_id = None

    state = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "focusedTabId": focus_id,
        "tabs": tabs,
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return state


def clear_tabs() -> None:
    state_path.write_text(
        json.dumps(
            {
                "updatedAt": datetime.now(timezone.utc).isoformat(),
                "focusedTabId": None,
                "tabs": [],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
