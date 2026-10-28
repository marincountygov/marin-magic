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
    page.wait_for_function("!/Reading/.test(document.querySelector('#file-status').textContent) && !document.querySelector('#mapping-panel').hidden && document.querySelector('#html-panel').textContent.length > 0")
    page.wait_for_timeout(100)


def run(browser, base, tmp: Path):
    context = browser.new_context(viewport={"width": 1100, "height": 900}, accept_downloads=True)
    context.grant_permissions(["clipboard-read", "clipboard-write"], origin=base.rstrip("/"))
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
    for button, name, check in (
        ("#download-html", "marinmagic-output.html", lambda t: "<h2>Ann</h2>" in t and "<script" not in t),
        ("#download-text", "marinmagic-output.txt", lambda t: t.startswith("Ann\nEmail: a@example.org") and "<" not in t.split("Cy")[0]),
        ("#download-md", "marinmagic-output.md", lambda t: t.startswith("## Ann\n\n- Email: a@example.org")),
    ):
        require(page.is_hidden("#download-panel"), "The Download menu starts closed")
        page.click("button[aria-controls=download-panel]")
        with page.expect_download() as info:
            page.click(button)
        require(info.value.suggested_filename == name, f"The download is named {name}: {info.value.suggested_filename}")
        saved = Path(info.value.path()).read_text(encoding="utf-8")
        require(check(saved), f"{name} has the generated content: {saved!r}")
    page.click("#reset-tool")
    page.wait_for_timeout(200)
    require(page.is_hidden("#mapping-panel") or "Ann" not in output(page), "Reset clears the result")

    open_file(page, write(tmp, "people.csv", CSV))
    # Copy is one button with a menu of formats; choosing one runs it and closes the menu.
    require(page.is_hidden("#copy-panel"), "The Copy menu starts closed")
    page.click("button[aria-controls=copy-panel]")
    names = page.locator("#copy-panel button").all_text_contents()
    require(names == ["HTML", "Text", "Markdown"], f"The Copy menu lists HTML, Text and Markdown, in the Download order: {names}")
    page.click("#copy-html")
    page.wait_for_function("document.querySelector('#file-status').textContent.includes('Copied HTML source')")
    require(page.is_hidden("#copy-panel"), "Choosing a format closes the Copy menu")
    page.click("button[aria-controls=copy-panel]")
    page.click("#copy-md")
    page.wait_for_function("document.querySelector('#file-status').textContent.includes('Copied Markdown')")
    require(page.evaluate("navigator.clipboard.readText()").startswith("## "), "Copy Markdown puts Markdown on the clipboard")

    # JSON input.
    open_file(page, write(tmp, "people.json", json.dumps([{"Name": "Dee", "Email": "d@example.org"}, {"Name": "Al", "Email": "al@example.org"}])))
    require(output(page).startswith("<h2>Al</h2>"), "JSON input works and is sorted")

    # Bad characters are fixed, not shown as errors: a Windows-1252 file (a curly apostrophe saved as one
    # byte), a UTF-8 file that already holds a replacement character, curly quotes, and a wrongly decoded apostrophe.
    legacy = tmp / "legacy.csv"
    legacy.write_bytes(b"Name,Note\nJimmy\x92s,Caf\xe9 \x93open\x94\n")
    open_file(page, str(legacy))
    html = output(page)
    require("<h2>Jimmy's</h2>" in html, f"A Windows-1252 apostrophe becomes a plain apostrophe: {html}")
    require("Caf\u00e9" in html and "&quot;open&quot;" in html, f"Accents are kept and curly quotes become plain: {html}")
    require(page.text_content("#file-status").strip() == "", "No message is shown about fixed characters")
    open_file(page, write(tmp, "broken.csv", "Name,Note\nJimmy\ufffds,It\u2019s \u00e2\u20ac\u2122fine\u2026\n"))
    html = output(page)
    require("<h2>Jimmy's</h2>" in html and "It's 'fine..." in html, f"A replacement character, curly apostrophes and mis-decoded text are fixed: {html}")
    require("\ufffd" not in html, "No replacement characters are left")

    # Unsupported file types are refused with a message.
    page.set_input_files("#file-input", write(tmp, "notes.txt", "hello"))
    page.wait_for_function("document.querySelector('#file-status').textContent.includes('Unsupported')")

    # Every button has a name; icon-only buttons also have a tooltip.
    unnamed = page.evaluate("""() => [...document.querySelectorAll('button, [role=button]')].filter(b => !(b.getAttribute('aria-label') || b.textContent || '').trim()).map(b => b.outerHTML.slice(0, 80))""")
    require(not unnamed, f"Every button has a name: {unnamed}")
    icon_only = page.evaluate("""() => [...document.querySelectorAll('button.action-button')].filter(b => !(b.textContent || '').trim() && !b.title).map(b => b.id)""")
    require(not icon_only, f"Icon-only buttons have a tooltip: {icon_only}")
    # The page is never wider than the window, desktop or phone.
    require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "No horizontal scroll at 1100 px")
    page.set_viewport_size({"width": 390, "height": 800})
    page.wait_for_timeout(200)
    require(page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1"), "No horizontal scroll at 390 px")
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
