#!/usr/bin/env python3
"""Show the latest tabs and helper-managed focus from open-tabs.json."""

import json

from tab_state import state_path


def main() -> None:
    if not state_path.exists():
        print("No open-tabs snapshot exists.")
        return

    state = json.loads(state_path.read_text())
    focused_tab_id = state.get("focusedTabId")
    for tab in state.get("tabs", []):
        marker = "*" if tab["id"] == focused_tab_id else " "
        print(f"{marker} {tab['id']} | {tab['title'] or '(untitled)'} | {tab['url']}")


if __name__ == "__main__":
    main()
