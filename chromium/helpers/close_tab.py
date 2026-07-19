#!/usr/bin/env python3
"""Close one tab in the running agent Chromium instance."""

import sys
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import urlopen

from tab_state import DEBUGGING_URL, activate_tab, focused_tab_id, list_tabs, snapshot_tabs


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: close_tab.py <target-id>")
        raise SystemExit(2)

    requested_id = sys.argv[1]
    target_id = quote(requested_id, safe="")

    try:
        with urlopen(f"{DEBUGGING_URL}/json/close/{target_id}", timeout=5) as response:
            print(response.read().decode().strip())
    except (HTTPError, URLError):
        print("Tab was not closed. Check that Agent Chromium and the target id exist.")
        raise SystemExit(1)

    focus_id = focused_tab_id()
    tabs = [tab for tab in list_tabs() if tab["type"] == "page"]
    if focus_id == requested_id:
        focus_id = tabs[0]["id"] if tabs else None
        if focus_id:
            activate_tab(focus_id)
    snapshot_tabs(focus_id)


if __name__ == "__main__":
    main()
