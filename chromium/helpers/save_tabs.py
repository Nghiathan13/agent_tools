#!/usr/bin/env python3
"""Save a snapshot of the currently open agent Chromium tabs."""

from urllib.error import HTTPError, URLError

from tab_state import snapshot_tabs, state_path


def main() -> None:
    try:
        snapshot_tabs()
    except (HTTPError, URLError):
        print("Agent Chromium is not running.")
        raise SystemExit(1)

    print(state_path)


if __name__ == "__main__":
    main()
