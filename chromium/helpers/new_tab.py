#!/usr/bin/env python3
"""Open a new tab in the running agent Chromium instance."""

import json
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

from tab_state import DEBUGGING_URL, activate_tab, snapshot_tabs


def open_tab(target_url: str) -> dict:
    request = Request(
        f"{DEBUGGING_URL}/json/new?{quote(target_url, safe=':/?&=#')}",
        method="PUT",
    )

    with urlopen(request, timeout=5) as response:
        return json.load(response)


def main() -> None:
    target_url = sys.argv[1] if len(sys.argv) > 1 else "about:blank"

    try:
        target = open_tab(target_url)
    except OSError:
        print("Agent Chromium is not running.")
        raise SystemExit(1)

    activate_tab(target["id"])
    snapshot_tabs(target["id"])
    print(json.dumps({"id": target["id"], "url": target["url"]}))


if __name__ == "__main__":
    main()
