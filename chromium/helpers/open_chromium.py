#!/usr/bin/env python3
"""Open one persistent Chromium instance for agent tools."""

import fcntl
import subprocess
import time
from http.client import HTTPException
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from patchright.sync_api import sync_playwright
DEBUGGING_URL = "http://127.0.0.1:9222"


def is_chromium_running() -> bool:
    try:
        with urlopen(f"{DEBUGGING_URL}/json/version", timeout=1):
            return True
    except (URLError, OSError, HTTPException):
        return False


def main() -> None:
    chromium_directory = Path(__file__).resolve().parents[1]
    profile_directory = chromium_directory / "profile"
    profile_directory.mkdir(exist_ok=True)

    with (profile_directory / ".startup.lock").open("w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)

        if is_chromium_running():
            print("Agent Chromium is already running.")
            return

        with sync_playwright() as playwright:
            browser = subprocess.Popen(
                [
                    playwright.chromium.executable_path,
                    f"--user-data-dir={profile_directory}",
                    "--remote-debugging-port=9222",
                    "--remote-debugging-address=127.0.0.1",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--restore-last-session",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        (profile_directory / "chromium.pid").write_text(str(browser.pid))
        for _ in range(10):
            if is_chromium_running():
                print("Agent Chromium is open.")
                return
            time.sleep(0.5)

        if browser.poll() is None:
            browser.terminate()
        raise SystemExit("Agent Chromium could not be started.")


if __name__ == "__main__":
    main()
