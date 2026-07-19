#!/usr/bin/env python3
"""Focus one existing agent Chromium tab."""

import json
import sys

from tab_state import activate_tab, list_tabs, snapshot_tabs


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: focus_tab.py <target-id>")
        raise SystemExit(2)

    target_id = sys.argv[1]
    target = next(
        (tab for tab in list_tabs() if tab["type"] == "page" and tab["id"] == target_id),
        None,
    )
    if target is None:
        print("Tab was not focused. Check that the target id exists.")
        raise SystemExit(1)

    activate_tab(target_id)
    snapshot_tabs(target_id)
    print(json.dumps({"id": target_id, "url": target["url"]}))


if __name__ == "__main__":
    main()
