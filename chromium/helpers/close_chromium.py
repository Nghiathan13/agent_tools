#!/usr/bin/env python3
"""Close the running agent Chromium instance."""

import os
import signal
import time
from pathlib import Path

from open_chromium import is_chromium_running
from tab_state import clear_tabs


def main() -> None:
    profile_directory = Path(__file__).resolve().parents[1] / "profile"
    pid_file = profile_directory / "chromium.pid"

    if not is_chromium_running():
        pid_file.unlink(missing_ok=True)
        clear_tabs()
        print("Agent Chromium is not running.")
        return

    try:
        os.kill(int(pid_file.read_text().strip()), signal.SIGTERM)
    except (OSError, ValueError):
        print("Agent Chromium could not be closed.")
        raise SystemExit(1)

    for _ in range(10):
        if not is_chromium_running():
            pid_file.unlink(missing_ok=True)
            clear_tabs()
            print("Agent Chromium is closed.")
            return
        time.sleep(0.5)

    print("Agent Chromium could not be closed.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
