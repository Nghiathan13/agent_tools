#!/usr/bin/env python3
"""Delete one saved ChatGPT session through the ChatGPT interface."""

import argparse
import json
import time
from urllib.error import HTTPError, URLError

from patchright.sync_api import sync_playwright

from open_chatgpt import (
    DEBUGGING_URL,
    ensure_chatgpt_tab,
    ensure_chromium,
    load_sessions,
    log,
    page_for_target,
    sessions_path,
    snapshot_tabs,
)


def remove_saved_session(session_id: str) -> None:
    sessions = load_sessions()
    remaining_sessions = [session for session in sessions if session["id"] != session_id]
    sessions_path.write_text(
        json.dumps({"version": 1, "sessions": remaining_sessions}, ensure_ascii=False, indent=2)
        + "\n"
    )


def wait_until_absent(page, session_id: str) -> None:
    link = page.locator(f'a[href="/c/{session_id}"]')
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if link.count() == 0:
            return
        time.sleep(0.25)
    raise RuntimeError("ChatGPT did not remove the conversation from the sidebar.")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("id")
    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()
    try:
        session = next(item for item in load_sessions() if item["id"] == arguments.id)
        if not ensure_chromium():
            log("Agent Chromium could not be started.")
            raise SystemExit(1)

        target_id, _ = ensure_chatgpt_tab()
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(DEBUGGING_URL)
            page = page_for_target(browser, target_id)
            page.goto(session["url"], wait_until="domcontentloaded", timeout=30_000)

            link = page.locator(f'a[href="/c/{arguments.id}"]')
            link.wait_for(state="visible", timeout=30_000)
            link.hover()
            page.locator(
                f'button[data-conversation-options-trigger="{arguments.id}"]'
            ).click()
            page.get_by_role("menuitem", name="Delete").click()

            dialog = page.locator('[role="dialog"]')
            dialog.wait_for(state="visible", timeout=10_000)
            if session["title"] and session["title"] not in dialog.inner_text():
                raise RuntimeError("Delete dialog does not match the saved session.")
            dialog.locator('button[data-testid="delete-conversation-confirm-button"]').click()
            dialog.wait_for(state="hidden", timeout=10_000)
            wait_until_absent(page, arguments.id)

            remove_saved_session(arguments.id)
            snapshot_tabs(target_id)
            print(f"Deleted session: {arguments.id}")
    except (HTTPError, URLError, RuntimeError, StopIteration) as error:
        log(str(error))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
