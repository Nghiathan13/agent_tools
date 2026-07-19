#!/usr/bin/env python3
"""Ask ChatGPT in the helper-managed focused tab."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from patchright.sync_api import sync_playwright

chromium_directory = Path(__file__).resolve().parents[1]
sessions_path = Path(__file__).resolve().parent / "sessions.json"
sys.path.insert(0, str(chromium_directory / "helpers"))

from new_tab import open_tab
from tab_state import (
    DEBUGGING_URL,
    activate_tab,
    focused_tab_id,
    list_tabs,
    snapshot_tabs,
)

CHATGPT_URL = "https://chatgpt.com/"
RESPONSE_START_TIMEOUT_SECONDS = 30


def log(message: str) -> None:
    print(message, file=sys.stderr)


def is_chromium_running() -> bool:
    try:
        with urlopen(f"{DEBUGGING_URL}/json/version", timeout=1):
            return True
    except URLError:
        return False


def ensure_chromium() -> bool:
    if is_chromium_running():
        return True

    subprocess.Popen(
        [
            str(chromium_directory / ".venv" / "bin" / "python"),
            str(chromium_directory / "helpers" / "open_chromium.py"),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    for _ in range(10):
        if is_chromium_running():
            return True
        time.sleep(0.5)
    return False


def load_sessions() -> list[dict]:
    if not sessions_path.exists():
        return []
    return json.loads(sessions_path.read_text())["sessions"]


def save_session(session_id: str, url: str, title: str) -> None:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    sessions = load_sessions()
    session = next((item for item in sessions if item["id"] == session_id), None)
    if session is None:
        sessions.append(
            {
                "id": session_id,
                "url": url,
                "title": title,
                "createdAt": now,
                "lastUsedAt": now,
            }
        )
    else:
        session["url"] = url
        session["title"] = title or session["title"]
        session["lastUsedAt"] = now
    sessions_path.write_text(
        json.dumps({"version": 1, "sessions": sessions}, ensure_ascii=False, indent=2)
        + "\n"
    )


def ensure_chatgpt_tab() -> str:
    tabs = {tab["id"]: tab for tab in list_tabs() if tab["type"] == "page"}
    target = tabs.get(focused_tab_id())
    if target and target["url"].startswith(CHATGPT_URL):
        activate_tab(target["id"])
        snapshot_tabs(target["id"])
        return target["id"]

    target = open_tab(CHATGPT_URL)
    activate_tab(target["id"])
    snapshot_tabs(target["id"])
    return target["id"]


def page_for_target(browser, target_id: str):
    for context in browser.contexts:
        for page in context.pages:
            cdp_session = context.new_cdp_session(page)
            try:
                target_info = cdp_session.send("Target.getTargetInfo")
                if target_info["targetInfo"]["targetId"] == target_id:
                    return page
            finally:
                cdp_session.detach()
    raise RuntimeError("Focused ChatGPT tab is unavailable.")


def sidebar_sessions(page) -> dict[str, dict[str, str]]:
    links = page.locator('a[href^="/c/"]').evaluate_all(
        "els => els.map(e => ({href: e.getAttribute('href'), title: e.innerText.trim()}))"
    )
    return {
        link["href"].split("/")[-1]: {
            "url": f"https://chatgpt.com{link['href']}",
            "title": link["title"],
        }
        for link in links
    }


def conversation_title(page, session_id: str) -> str:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        session = sidebar_sessions(page).get(session_id)
        if session and session["title"]:
            return session["title"]
        time.sleep(0.25)
    return ""


def session_id_from_url(url: str) -> str | None:
    path = urlparse(url).path.strip("/").split("/")
    if len(path) == 2 and path[0] == "c":
        return path[1]
    return None


def wait_for_new_session(target_id: str, previous_ids: set[str], timeout_seconds: int) -> tuple[str, str]:
    deadline = time.monotonic() + min(RESPONSE_START_TIMEOUT_SECONDS, timeout_seconds)
    while time.monotonic() < deadline:
        target = next((tab for tab in list_tabs() if tab["id"] == target_id), None)
        url = target["url"] if target else ""
        session_id = session_id_from_url(url)
        if session_id and session_id not in previous_ids:
            return session_id, url
        time.sleep(0.25)
    raise RuntimeError("ChatGPT did not create a conversation within 30 seconds.")


def wait_for_session_history(page) -> None:
    deadline = time.monotonic() + RESPONSE_START_TIMEOUT_SECONDS
    messages = page.locator('[data-message-author-role]')
    while time.monotonic() < deadline:
        if messages.count():
            return
        time.sleep(0.25)
    raise RuntimeError("Saved ChatGPT session did not load within 30 seconds.")


def wait_for_response(page, previous_assistants: int, previous_copies: int, timeout_seconds: int) -> str:
    assistants = page.locator('[data-message-author-role="assistant"]')
    copies = page.locator('button[aria-label="Copy response"]')
    start_deadline = time.monotonic() + min(RESPONSE_START_TIMEOUT_SECONDS, timeout_seconds)
    while time.monotonic() < start_deadline:
        if assistants.count() > previous_assistants:
            break
        time.sleep(0.25)
    else:
        raise RuntimeError("ChatGPT did not start a response within 30 seconds.")

    end_deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < end_deadline:
        if copies.count() > previous_copies:
            return assistants.nth(-1).inner_text().strip()
        time.sleep(0.5)
    raise RuntimeError(f"ChatGPT response did not finish within {timeout_seconds} seconds.")


def ask(page, target_id: str, prompt: str, timeout_seconds: int, session: dict | None) -> str:
    if session:
        wait_for_session_history(page)

    assistants = page.locator('[data-message-author-role="assistant"]')
    copies = page.locator('button[aria-label="Copy response"]')
    previous_assistants = assistants.count()
    previous_copies = copies.count()
    previous_session_ids = set(sidebar_sessions(page))

    editor = page.locator('[contenteditable="true"]')
    editor.wait_for(state="visible", timeout=10_000)
    editor.click()
    editor.press_sequentially(prompt)
    editor.press("Enter")

    if session:
        session_id, url = session["id"], session["url"]
    else:
        session_id, url = wait_for_new_session(target_id, previous_session_ids, timeout_seconds)

    save_session(session_id, url, conversation_title(page, session_id))
    response = wait_for_response(page, previous_assistants, previous_copies, timeout_seconds)
    save_session(session_id, url, conversation_title(page, session_id))
    return response


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    new_session = commands.add_parser("new-session")
    new_session.add_argument("prompt")
    new_session.add_argument("--timeout", type=int, default=300)
    session = commands.add_parser("session")
    session.add_argument("id")
    session.add_argument("prompt")
    session.add_argument("--timeout", type=int, default=300)
    arguments = parser.parse_args()
    if arguments.timeout < RESPONSE_START_TIMEOUT_SECONDS:
        parser.error("--timeout must be at least 30 seconds")
    return arguments


def main() -> None:
    arguments = parse_arguments()
    if not ensure_chromium():
        log("Agent Chromium could not be started.")
        raise SystemExit(1)

    try:
        session = None
        target_url = CHATGPT_URL
        if arguments.command == "session":
            session = next(item for item in load_sessions() if item["id"] == arguments.id)
            target_url = session["url"]

        target_id = ensure_chatgpt_tab()
        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(DEBUGGING_URL)
            page = page_for_target(browser, target_id)
            page.goto(target_url, wait_until="domcontentloaded", timeout=30_000)
            page.bring_to_front()
            snapshot_tabs(target_id)
            print(ask(page, target_id, arguments.prompt, arguments.timeout, session))
            snapshot_tabs(target_id)
    except (HTTPError, URLError, RuntimeError, StopIteration) as error:
        log(str(error))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
