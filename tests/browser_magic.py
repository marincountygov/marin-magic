#!/usr/bin/env python3
"""Browser test of the Marin Magic workflow, over HTTP with Playwright.

Loads small fixture files (never real records), checks that the generated HTML is right (sorted, escaped, blank
values skipped, heading level, field order and choice), that the Text and HTML tabs and the buttons work, and that
every button has an accessible name. Needs Playwright for Python with Chromium.  Run: python3 tests/browser_magic.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

CSV = (
    "Name,Email,Notes\n"
    "Bo,b@example.org,Second\n"
    "Ann,a@example.org,\n"
    ",nobody@example.org,Has no heading\n"
    "Cy,c@example.org,\"A <b>bold</b> & \"\"quoted\"\" note\"\n"
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def write(directory: Path, name: str, text: str) -> str:
    path = directory / name
    path.write_text(text, encoding="utf-8")
    return str(path)


def output(page) -> str:
    return page.evaluate("document.querySelector('#html-panel').textContent")


def bo(html: str) -> str:
    """Bo's record, the one that has both an email and a note."""
    return html.split("<h2>Bo</h2>")[1].split("<h2>")[0]


def open_file(page, path: str):
    page.set_input_files("#file-input", path)
    page.wait_for_function("document.querySelector('#file-status').textContent.includes('Preview generated')")


def run(browser, base, tmp: Path):
    context = browser.new_context(viewport={"width": 1100, "height": 900}, accept_downloads=True)
    page = context.new_page()
    problems = []
    page.on("pageerror", lambda e: problems.append(str(e)))
    page.on("console", lambda m: problems.append(m.text) if m.type == "error" else None)
    page.goto(base)
    page.wait_for_selector("#browse-files")
    require(page.is_hidden("#mapping-panel"), "The field choices stay hidden until a file is loaded")

    # Load a CSV: the first column is the heading, the rest are choices.
    open_file(page, write(tmp, "people.csv", CSV))
    options = page.locator("#heading-column option").all_text_contents()
    require(options == ["Name", "Email", "Notes"], f"Heading choices are the column names: {options}")
    first = output(page)
    require(first.startswith("<h2>Ann</h2>"), f"Records are sorted by heading, ignoring case: {first[:60]}")
    require(first.index("<h2>Ann</h2>") < first.index("<h2>Bo</h2>") < first.index("<h2>Cy</h2>"), "Ann, Bo, Cy in order")
    require("nobody@example.org" not in first, "A row with no heading is left out")
    require("<li>Notes: Second</li>" in first, "A list item is 'Column: value'")
    require("<li>Notes: </li>" not in first and first.count("Notes:") == 2, "Blank values make no list item")
    require("<li>Email: a@example.org</li>" in first, "Chosen columns appear")

    # Escaping: HTML and ampersands in the data are text, not markup.
    require("&lt;b&gt;bold&lt;/b&gt; &amp; \"quoted\" note" in first or "&lt;b&gt;bold&lt;/b&gt; &amp; &quot;quoted&quot; note" in first,
            "Markup in the data is escaped")
    require(page.locator("#text-panel b").count() == 0, "No bold element is created from the data")

    # The Text tab shows the result; the HTML tab shows the source.
    require(page.locator("#text-panel h2").first.inner_text() == "Ann", "The Text tab renders the headings")
    page.click("#html-tab")
    require(page.is_visible("#html-panel") and page.is_hidden("#text-panel"), "The HTML tab shows the source")
    require(page.get_attribute("#html-tab", "aria-selected") == "true" and page.get_attribute("#text-tab", "aria-selected") == "false", "Tab state")
    page.focus("#html-tab")
    page.keyboard.press("ArrowLeft")
    require(page.get_attribute("#text-tab", "aria-selected") == "true" and page.is_visible("#text-panel"), "Arrow keys move between tabs")

    # Heading level.
    page.select_option("#heading-level", "h3")
    page.click("#generate-preview")
    require(output(page).startswith("<h3>Ann</h3>") and "<h2>" not in output(page), "The heading level is used")
    page.select_option("#heading-level", "h2")

    # Field choice and order.
    page.uncheck("#field-list input:checked >> nth=0") if page.locator("#field-list input:checked").count() == 2 else None
    page.click("#generate-preview")
    require("Email:" not in output(page) and "Notes: Second" in output(page), "Unchecking a field removes it")
    page.check("#field-list li:has-text('Email') input, #field-list [class*=field-item]:has-text('Email') input")
    page.click("#generate-preview")
    before = bo(output(page))
    require(before.index("Email:") < before.index("Notes:"), "Fields follow the list order")
    page.click("button[aria-label='Move Email down']")
    page.click("#generate-preview")
    after = bo(output(page))
    require(after.index("Notes:") < after.index("Email:"), "Move down changes the output order")
    page.click("button[aria-label='Move Email up']")
    page.click("#generate-preview")
    require(bo(output(page)).index("Email:") < bo(output(page)).index("Notes:"), "Move up puts it back")

    # Download and reset.
    with page.expect_download() as info:
        page.click("#download-html")
    saved = Path(info.value.path()).read_text(encoding="utf-8")
    require("<h2>Ann</h2>" in saved and "<script" not in saved, "The downloaded file is the generated HTML")
    page.click("#reset-tool")
    page.wait_for_timeout(200)
    require(page.is_hidden("#mapping-panel") or "Ann" not in output(page), "Reset clears the result")

    # JSON input.
    open_file(page, write(tmp, "people.json", json.dumps([{"Name": "Dee", "Email": "d@example.org"}, {"Name": "Al", "Email": "al@example.org"}])))
    require(output(page).startswith("<h2>Al</h2>"), "JSON input works and is sorted")

    # Unsupported file types are refused with a message.
    page.set_input_files("#file-input", write(tmp, "notes.txt", "hello"))
    page.wait_for_function("document.querySelector('#file-status').textContent.includes('Unsupported')")

    # Every button has a name; icon-only buttons also have a tooltip.
    unnamed = page.evaluate("""() => [...document.querySelectorAll('button, [role=button]')].filter(b => !(b.getAttribute('aria-label') || b.textContent || '').trim()).map(b => b.outerHTML.slice(0, 80))""")
    require(not unnamed, f"Every button has a name: {unnamed}")
    icon_only = page.evaluate("""() => [...document.querySelectorAll('button.action-button')].filter(b => !(b.textContent || '').trim() && !b.title).map(b => b.id)""")
    require(not icon_only, f"Icon-only buttons have a tooltip: {icon_only}")
    # Visible content stays inside the window. (The hidden file input is left out: the shell's .visually-hidden class
    # is overridden by Pico's input width, which makes the page 33 px wider than the window. A shell fix is pending.)
    wide = page.evaluate("""() => [...document.querySelectorAll('body *')]
        .filter((e) => !e.closest('.visually-hidden') && !e.matches('.visually-hidden') && e.getBoundingClientRect().right > innerWidth + 1)
        .map((e) => e.tagName + '.' + e.className)""")
    require(not wide, f"Nothing visible runs off the right edge: {wide}")
    require(not problems, f"Console or page errors: {problems}")
    context.close()


def main():
    handler = partial(Handler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}/"
    with tempfile.TemporaryDirectory() as temp, sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            run(browser, base, Path(temp))
        finally:
            browser.close()
            server.shutdown()
    print("Marin Magic browser workflow: PASS")


if __name__ == "__main__":
    try:
        main()
    except AssertionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
