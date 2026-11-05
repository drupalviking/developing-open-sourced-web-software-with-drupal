#!/usr/bin/env python3
"""Takes the book's screenshots from the test sites, so they can be retaken when Drupal changes.

The test sites are DDEV projects outside this repository (see PROJECT-LOG.md,
"Where we are"): `lens-and-trail` (Drupal core) and `lens-and-trail-cms`
(Drupal CMS). Each must be running, and in the state the chapter leaves it in.
The script only looks: it fills in forms to show them, but never saves them.

Screenshots are taken at twice the size (for sharp text) and resized to 1280
pixels wide, into manuscript/images/.

Usage:
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt
  .venv/bin/playwright install chromium        # once: Playwright's own browser
  .venv/bin/python tools/screenshots.py              # every screenshot
  .venv/bin/python tools/screenshots.py 06           # one chapter
  .venv/bin/python tools/screenshots.py 06-revisions # one screenshot

Set CORE_URL or CMS_URL if your sites have other addresses (on the author's
machine, DDEV's router uses port 8443).
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT / "manuscript" / "images"
WIDTH = 1280

SITES = {
    "core": {
        "url": os.environ.get("CORE_URL", "https://lens-and-trail.ddev.site:8443"),
        "user": "admin",
        "password": "12345",
    },
    "cms": {
        "url": os.environ.get("CMS_URL", "https://lens-and-trail-cms.ddev.site:8443"),
        "user": "admin@lens-and-trail-cms.ddev.site",
        "password": "12345",
    },
}


# What each screenshot shows. Each function gets a logged-in page (or a
# logged-out one, if the shot says so) and the site's address, and leaves the
# page as it should be photographed.

def add_content_type(page: Page, url: str) -> None:
    page.goto(url + "/admin/structure/types/add")
    page.fill("#edit-name", "Basic page")
    page.wait_for_timeout(1500)
    page.click(".machine-name-label button, button:has-text('Edit')")
    page.fill("#edit-type", "page")
    page.fill("#edit-description", "Use Basic page for content that rarely changes, such as About the club or How to join.")
    page.click("text=Display settings")
    page.uncheck("#edit-display-submitted")
    page.click("text=Submission form settings")


def add_field(page: Page, url: str) -> None:
    page.goto(url + "/admin/structure/types/manage/page/fields")
    page.click("text=Create a new field")
    page.wait_for_selector(".ui-dialog")
    page.wait_for_timeout(1500)


def content_form(page: Page, url: str) -> None:
    page.goto(url + "/node/1/edit")
    page.click("summary:has-text('Menu settings')")
    page.click("summary:has-text('URL alias')")
    page.wait_for_timeout(500)
    page.locator("#edit-path-0-alias").scroll_into_view_if_needed()


def front_page_setting(page: Page, url: str) -> None:
    page.goto(url + "/admin/config/system/site-information")
    page.locator("#edit-site-frontpage").scroll_into_view_if_needed()


def revisions(page: Page, url: str) -> None:
    page.goto(url + "/node/1/revisions")


def moderation_state(page: Page, url: str) -> None:
    page.goto(url + "/node/1/edit")
    page.locator("select[name='moderation_state[0][state]']").scroll_into_view_if_needed()


def layout_builder(page: Page, url: str) -> None:
    page.goto(url + "/node/2/layout")
    page.wait_for_load_state("networkidle")
    page.locator("text=Add section").first.evaluate("e => window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - 120)")


def visitor(path: str):
    def show(page: Page, url: str) -> None:
        page.goto(url + path)
    return show


def canvas_editor(page: Page, url: str) -> None:
    page.goto(url + "/canvas/editor/canvas_page/2")
    page.wait_for_timeout(6000)
    page.click("button[aria-label='Library']")
    page.wait_for_timeout(1500)


def trash(page: Page, url: str) -> None:
    page.goto(url + "/admin/content/trash")


# name: (site, function, logged in, full page[, window width])
SHOTS = {
    "06-add-content-type": ("core", add_content_type, True, False),
    "06-add-field": ("core", add_field, True, False),
    "06-content-form": ("core", content_form, True, False),
    "06-front-page-setting": ("core", front_page_setting, True, False),
    "06-front-page": ("core", visitor("/"), False, False),
    "06-revisions": ("core", revisions, True, False),
    "06-moderation-state": ("core", moderation_state, True, False),
    "06-layout-builder": ("core", layout_builder, True, False),
    "06-how-to-join": ("core", visitor("/join"), False, False),
    "06-canvas-editor": ("cms", canvas_editor, True, False, 1600),
    "06-canvas-how-to-join": ("cms", visitor("/join"), False, False),
    "06-trash": ("cms", trash, True, False),
}


def log_in(page: Page, site: dict) -> None:
    page.goto(site["url"] + "/user/login")
    page.fill("#edit-name", site["user"])
    page.fill("#edit-pass", site["password"])
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")


def main(wanted: list[str]) -> int:
    names = [n for n in SHOTS if not wanted or any(n == w or n.startswith(w + "-") for w in wanted)]
    if not names:
        print(f"No screenshots match {' '.join(wanted)}.")
        return 1
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        contexts = {}
        for name in names:
            site_name, show, logged_in, full_page, *rest = SHOTS[name]
            width = rest[0] if rest else WIDTH
            site = SITES[site_name]
            key = (site_name, logged_in, width)
            if key not in contexts:
                context = browser.new_context(viewport={"width": width, "height": 900}, device_scale_factor=2, ignore_https_errors=True)
                if logged_in:
                    log_in(context.new_page(), site)
                contexts[key] = context
            page = contexts[key].new_page()
            show(page, site["url"])
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(500)
            target = IMAGES / f"{name}.png"
            page.screenshot(path=str(target), full_page=full_page)
            page.close()
            subprocess.run(["sips", "--resampleWidth", str(WIDTH), str(target)], check=True, capture_output=True)
            print(f"{target.relative_to(ROOT)}")
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
