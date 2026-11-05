#!/usr/bin/env python3
"""Takes the book's screenshots from the test sites, so they can be retaken when Drupal changes.

The test sites are DDEV projects outside this repository (see PROJECT-LOG.md,
"Where we are"): `lens-and-trail` (Drupal core) and `lens-and-trail-cms`
(Drupal CMS). Each must be running, and in the state the chapter leaves it in.
The script only looks: it fills in forms to show them, but never saves them.
The exception is a step-by-step sequence (re-using a field, Layout Builder,
Canvas), which changes the site as it goes: it works on a temporary copy, made with
`ddev drush` in the site's directory, and deletes the copy when it's done.

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
machine, DDEV's router uses port 8443), and CORE_DIR or CMS_DIR if their
DDEV projects aren't in ~/websites/open-university/.
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
        "dir": os.environ.get("CORE_DIR", str(Path.home() / "websites/open-university/lens-and-trail")),
        "user": "admin",
        "password": "12345",
    },
    "cms": {
        "url": os.environ.get("CMS_URL", "https://lens-and-trail-cms.ddev.site:8443"),
        "dir": os.environ.get("CMS_DIR", str(Path.home() / "websites/open-university/lens-and-trail-cms")),
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


def add_field_type(page: Page, url: str) -> None:
    add_field(page, url)
    page.click(".ui-dialog >> text=Formatted text")
    page.wait_for_timeout(1500)
    page.fill(".ui-dialog input[name='label']", "Body")
    page.wait_for_timeout(1500)
    page.click(".ui-dialog label:has-text('Long text')")


def add_field_settings(page: Page, url: str) -> None:
    # The site already has field_body, so give the field a throwaway machine
    # name: this step doesn't show it, and nothing is created until Save.
    add_field_type(page, url)
    page.click(".ui-dialog button:has-text('Edit')")
    page.fill(".ui-dialog input[name='field_name']", "screenshot_only")
    page.click(".ui-dialog button:has-text('Continue')")
    page.wait_for_selector(".ui-dialog-title:has-text('settings')")
    page.wait_for_timeout(1500)


def manage_fields(page: Page, url: str) -> None:
    page.goto(url + "/admin/structure/types/manage/page/fields")


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


def drush_php(site: dict, php: str) -> str:
    result = subprocess.run(["ddev", "drush", "php:eval", php], cwd=site["dir"], check=True, capture_output=True, text=True)
    return result.stdout.strip()


def scroll_to(page: Page, selector: str, offset: int = 120) -> None:
    page.locator(selector).first.evaluate(f"e => window.scrollTo(0, e.getBoundingClientRect().top + window.scrollY - {offset})")
    page.wait_for_timeout(400)


def layout_builder_steps(page: Page, site: dict, snap) -> None:
    """Chapter 8's Layout Builder steps, on a copy of How to join (node 2)."""
    nid = drush_php(site, '$n = \\Drupal\\node\\Entity\\Node::load(2)->createDuplicate(); $n->set("layout_builder__layout", []); $n->set("path", ["alias" => ""]); $n->set("moderation_state", "published"); $n->save(); echo $n->id();')
    url = site["url"]

    def panel_submit() -> None:
        page.click("#drupal-off-canvas input.form-submit.button--primary")
        page.wait_for_timeout(3500)
        page.wait_for_load_state("networkidle")

    try:
        page.goto(f"{url}/node/{nid}/layout")
        page.wait_for_load_state("networkidle")
        scroll_to(page, "h1")
        snap("08-lb-start")
        page.click("a:has-text('Add section')")
        page.wait_for_timeout(2500)
        snap("08-lb-choose-layout")
        page.click("#drupal-off-canvas a:has-text('Two column')")
        page.wait_for_timeout(2500)
        page.select_option("#drupal-off-canvas select", "67-33")
        snap("08-lb-column-widths")
        panel_submit()
        page.locator("a:has-text('Add block')").nth(1).click()
        page.wait_for_timeout(3000)
        snap("08-lb-choose-block")
        page.click("#drupal-off-canvas a:has-text('Create content block')")
        page.wait_for_timeout(3000)
        page.fill("#drupal-off-canvas input[name='settings[label]']", "When and where")
        page.evaluate("h => document.querySelector('#drupal-off-canvas .ck-editor__editable').ckeditorInstance.setData(h)", MEETING_TIMES)
        snap("08-lb-content-block")
        panel_submit()
        page.locator("a:has-text('Add block')").nth(0).click()
        page.wait_for_timeout(3000)
        page.click("#drupal-off-canvas a:text-is('Body')")
        page.wait_for_timeout(3000)
        page.select_option("#drupal-off-canvas select[name='settings[formatter][label]']", "hidden")
        snap("08-lb-body-block")
        panel_submit()
        page.click("a:has-text('Remove Section 2')")
        page.wait_for_timeout(3000)
        snap("08-lb-remove-section")
        panel_submit()
        page.fill("textarea[name='revision_log[0][value]']", "Two columns, with the meeting times on the right.")
        scroll_to(page, "h1")
        snap("08-lb-save")
    finally:
        drush_php(site, f'\\Drupal\\node\\Entity\\Node::load({nid})->delete();')


def canvas_steps(page: Page, site: dict, snap) -> None:
    """Chapter 8's Canvas steps, on a new Canvas page, deleted afterwards."""
    url = site["url"]
    page.goto(url + "/admin/content/pages")
    page.click("a:has-text('Add Page')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(6000)
    editor = page.url
    page_id = editor.rstrip("/").split("/")[-1]

    def reload() -> None:
        # Scale to fit zooms the preview; a fresh load puts it back at 100%,
        # where the drop positions below are measured.
        page.goto(editor)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(6000)

    def open_panel(label: str, marker: str) -> None:
        if not page.get_by_text(marker, exact=True).first.is_visible():
            page.click(f"button[aria-label='{label}']")
            page.wait_for_timeout(1000)

    def fit() -> None:
        page.click("[data-testid='scale-to-fit']")
        page.wait_for_timeout(1500)

    def drag(name: str, x: float, y: float) -> None:
        open_panel("Library", "Components")
        box = page.get_by_text(name, exact=True).first.bounding_box()
        page.mouse.move(box["x"] + 20, box["y"] + 8)
        page.mouse.down()
        for i in range(1, 25):
            page.mouse.move(box["x"] + 20 + (x - box["x"] - 20) * i / 24, box["y"] + 8 + (y - box["y"] - 8) * i / 24)
            page.wait_for_timeout(40)
        page.wait_for_timeout(700)
        page.mouse.up()
        page.wait_for_timeout(3500)

    def in_preview(selector: str, last: bool = False) -> dict:
        for frame in page.frames[1:]:
            boxes = [frame.locator(selector).nth(i).bounding_box() for i in range(frame.locator(selector).count())]
            boxes = [b for b in boxes if b and b["width"] > 0]
            if boxes:
                return boxes[-1] if last else boxes[0]
        raise RuntimeError(f"{selector} not found in the Canvas preview")

    def set_field(suffix: str, value: str) -> None:
        field = page.locator(f"input[name$='{suffix}']")
        field.fill(value)
        field.press("Tab")
        page.wait_for_timeout(1500)

    def set_rich_text(html: str) -> None:
        page.evaluate("h => [...document.querySelectorAll('.ck-editor__editable')].pop().ckeditorInstance.setData(h)", html)
        page.locator(".ck-editor__editable").last.click()
        page.keyboard.press("End")
        page.wait_for_timeout(2500)

    def layer_menu(row: str, *path: str) -> None:
        open_panel("Layers", "Mercury theme")
        page.get_by_text(row, exact=True).first.click(button="right")
        page.wait_for_timeout(800)
        for item in path:
            page.get_by_role("menuitem", name=item).hover()
            page.wait_for_timeout(700)

    try:
        set_field("title[0][value]", "How to join")
        alias = page.locator("input[name='path[0][alias]']")
        alias.fill("/join")
        snap("08-canvas-page-data")
        # The real How to join already has /join, so the copy gets another alias.
        alias.fill("/join-screenshot")
        alias.press("Tab")
        page.wait_for_timeout(2000)
        placeholder = page.get_by_text("Place items here").bounding_box()
        drag("Heading", placeholder["x"] + 40, placeholder["y"] + 5)
        set_field("[heading_text][0][value]", "How to join")
        page.select_option("select[name$='[level]']", "1")
        page.wait_for_timeout(2500)
        fit()
        snap("08-canvas-heading")
        page.get_by_text("Layout", exact=True).first.click()
        heading = in_preview("h1")
        drag("Grid", heading["x"] + 150, heading["y"] + heading["height"] - 4)
        page.select_option("select[name$='[columns]']", "2 columns 67%-33%")
        page.wait_for_timeout(2500)
        fit()
        snap("08-canvas-grid")
        reload()
        heading = in_preview("h1")
        drag("Text", heading["x"] + 500, heading["y"] + heading["height"] + 20)
        set_rich_text(HOW_TO_JOIN.replace("lens-and-trail.ddev.site", "lens-and-trail-cms.ddev.site"))
        fit()
        snap("08-canvas-text")
        # Dropped below the text, the card lands after the grid; move it in.
        reload()
        text = in_preview("p:has-text('Membership')")
        # Where a drop near the grid lands varies a little: try a few heights
        # until the card sits after the grid, so "Move into" offers the grid.
        for dy in (-4, -12, 4, -24, 12):
            drag("Icon card", text["x"] + 300, text["y"] + text["height"] + dy)
            open_panel("Layers", "Mercury theme")
            if not page.get_by_text("Icon card", exact=True).first.is_visible():
                continue  # The drop missed: try again.
            layer_menu("Icon card", "Move", "Move into")
            if page.get_by_role("menuitem", name="Grid (Grid)").count():
                break
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            layer_menu("Icon card")
            page.get_by_role("menuitem", name="Delete").click()
            page.wait_for_timeout(2500)
        else:
            raise RuntimeError("Couldn't drop the Icon card after the grid")
        snap("08-canvas-move")
        page.get_by_role("menuitem", name="Grid (Grid)").click()
        page.wait_for_timeout(3000)
        layer_menu("Text", "Move")
        page.get_by_role("menuitem", name="Move up").click()
        page.wait_for_timeout(3000)
        page.get_by_text("Icon card", exact=True).first.click()
        page.wait_for_timeout(2500)
        set_field("[icon][0][value]", "calendar-dots")
        set_field("[text][0][value]", "When and where")
        page.select_option("select[name$='[text_align]']", "left")
        page.wait_for_timeout(1500)
        set_rich_text(MEETING_TIMES)
        fit()
        snap("08-canvas-card")
        page.click("button:has-text('Review')")
        page.wait_for_timeout(2500)
        page.get_by_text("Select All").click()
        page.wait_for_timeout(800)
        snap("08-canvas-publish")
    except Exception:
        if os.environ.get("DEBUG_SHOT"):
            page.screenshot(path=os.environ["DEBUG_SHOT"])
        raise
    finally:
        drush_php(site, f'\\Drupal::service("trash.manager")->executeInTrashContext("inactive", fn() => \\Drupal::entityTypeManager()->getStorage("canvas_page")->load({page_id})->delete());')


HOW_TO_JOIN = (
    "<p>Come along to one of our hikes or photo evenings first, to see whether the club is for you. You don't need to tell us in advance.</p>"
    "<p>If you'd like to become a member, talk to the secretary on the day, or send an email to hello@lens-and-trail.ddev.site.</p>"
    "<p>Membership is £20 a year (£10 for students). It covers the room for the photo evenings and the club's insurance for the hikes.</p>"
)
MEETING_TIMES = (
    "<p>Hikes: every other Saturday, at 9:30. We send the meeting place to everyone who is coming a week before.</p>"
    "<p>Photo evenings: the first Thursday of the month, at 19:00, in the back room of a café in Leith.</p>"
)


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


# Chapter 7

def add_hike(page: Page, url: str) -> None:
    page.goto(url + "/admin/structure/types/add")
    page.fill("#edit-name", "Hike")
    page.wait_for_timeout(1500)
    page.fill("#edit-description", "A hike or photo walk the club organizes, with its date, meeting place, distance and difficulty.")
    page.click("text=Display settings")
    page.uncheck("#edit-display-submitted")
    page.click("text=Menu settings")
    page.uncheck("input[name='menu_options[main]']")


def hike_field_dialog(page: Page, url: str, field_type: str, label: str, choice: str, settings: bool = True) -> None:
    """The Add field window on Hike. The site already has these fields, so the
    settings step gets a throwaway machine name: nothing is created until Save."""
    page.goto(url + "/admin/structure/types/manage/hike/fields")
    page.click("text=Create a new field")
    page.wait_for_selector(".ui-dialog")
    page.wait_for_timeout(1500)
    page.click(f".ui-dialog >> text={field_type}")
    page.wait_for_timeout(1500)
    page.fill(".ui-dialog input[name='label']", label)
    page.wait_for_timeout(1500)
    page.click(f".ui-dialog label:has-text('{choice}')")
    if not settings:
        return
    page.click(".ui-dialog button:has-text('Edit')")
    page.fill(".ui-dialog input[name='field_name']", "screenshot_only")
    page.click(".ui-dialog button:has-text('Continue')")
    page.wait_for_selector(".ui-dialog-title:has-text('settings')")
    page.wait_for_timeout(1500)


def dialog_fill(page: Page, name: str, value: str) -> None:
    field = page.locator(f".ui-dialog [name='{name}']")
    field.fill(value)
    field.press("Tab")
    page.wait_for_timeout(1500)


def dialog_scroll_to(page: Page, selector: str) -> None:
    page.locator(f".ui-dialog {selector}").first.scroll_into_view_if_needed()
    page.wait_for_timeout(500)


def add_date(page: Page, url: str) -> None:
    hike_field_dialog(page, url, "Date and time", "Date", "Datetime", settings=False)


def date_settings(page: Page, url: str) -> None:
    hike_field_dialog(page, url, "Date and time", "Date", "Datetime")
    dialog_fill(page, "description", "The day and time we meet.")
    page.check(".ui-dialog input[name='required']")


def distance_settings(page: Page, url: str) -> None:
    hike_field_dialog(page, url, "Number", "Distance", "Decimal")
    dialog_fill(page, "field_storage[subform][settings][scale]", "1")
    dialog_fill(page, "description", "The length of the walk, in kilometers.")
    dialog_fill(page, "settings[min]", "0")
    dialog_fill(page, "settings[suffix]", " km")
    dialog_scroll_to(page, "[name='settings[suffix]']")


def difficulty_settings(page: Page, url: str) -> None:
    hike_field_dialog(page, url, "Selection list", "Difficulty", "Text")
    for i, name in enumerate(["Easy", "Moderate", "Hard"]):
        if i:
            page.click(".ui-dialog input[name='add_more_allowed_values']")
            page.wait_for_timeout(2500)
        dialog_fill(page, f"field_storage[subform][settings][allowed_values][table][{i}][item][label]", name)
    dialog_scroll_to(page, "[name='field_storage[subform][settings][allowed_values][table][0][item][label]']")


def hike_leader_settings(page: Page, url: str) -> None:
    hike_field_dialog(page, url, "Reference", "Hike leader", "User")
    dialog_fill(page, "description", "The member who leads the hike.")
    page.select_option(".ui-dialog select[name='settings[handler_settings][sort][field]']", "name")
    page.wait_for_timeout(2000)
    page.uncheck(".ui-dialog input[name='settings[handler_settings][include_anonymous]']")
    dialog_scroll_to(page, "[name='settings[handler_settings][sort][field]']")


def hike_fields(page: Page, url: str) -> None:
    page.goto(url + "/admin/structure/types/manage/hike/fields")


def hike_form_display(page: Page, url: str) -> None:
    page.goto(url + "/admin/structure/types/manage/hike/form-display")


def hike_form(page: Page, url: str) -> None:
    page.goto(url + "/node/add/hike")
    page.fill("input[name='title[0][value]']", "Turnhouse Hill and Carnethy Hill")
    page.fill("input[name='field_date[0][value][date]']", "2026-11-21")
    page.fill("input[name='field_date[0][value][time]']", "09:30")
    page.fill("input[name='field_meeting_place[0][value]']", "Flotterstone car park")
    page.fill("input[name='field_distance[0][value]']", "11.5")
    page.check("input[name='field_difficulty'][value='moderate']")
    page.select_option("select[name='field_hike_leader']", label="admin")
    page.evaluate("h => document.querySelector('.ck-editor__editable').ckeditorInstance.setData(h)", TURNHOUSE_HILL)
    page.click("summary:has-text('URL alias')")
    page.fill("input[name='path[0][alias]']", "/hikes/turnhouse-hill")
    page.select_option("select[name='moderation_state[0][state]']", "published")


def hike_permissions(page: Page, url: str) -> None:
    page.goto(url + "/admin/structure/types/manage/hike/permissions")


def cms_utility_page_fields(page: Page, url: str) -> None:
    page.goto(url + "/admin/structure/types/manage/page/fields")


TURNHOUSE_HILL = (
    "<p>Two of the best-known tops in the Pentland Hills, with views over Edinburgh and the Firth of Forth on a clear day. We climb steadily from Flotterstone to Turnhouse Hill, follow the ridge to Carnethy Hill, and come back down through the glen.</p>"
    "<p>Bring boots, a waterproof jacket, something warm, lunch, and your camera. The path is steep in places and can be muddy.</p>"
)


def reuse_field_steps(page: Page, site: dict, snap) -> None:
    """Chapter 7's re-use steps, on a temporary content type called Hike."""
    drush_php(site, '\\Drupal\\node\\Entity\\NodeType::create(["type" => "hike_screenshot", "name" => "Hike"])->save();')
    try:
        page.goto(site["url"] + "/admin/structure/types/manage/hike_screenshot/fields")
        page.click("text=Re-use an existing field")
        page.wait_for_selector(".ui-dialog")
        page.wait_for_timeout(2000)
        # When the reader gets here, Body is the only field to re-use; the
        # finished site has more, so the window shows only Body's row.
        page.evaluate("() => document.querySelectorAll('.ui-dialog tbody tr').forEach(r => { if (!r.textContent.includes('field_body')) r.remove(); })")
        snap("07-reuse-field")
        page.locator(".ui-dialog tr", has_text="field_body").locator("input, button").first.click()
        page.wait_for_url("**/node.hike_screenshot.field_body")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='label']", "Description")
        page.fill("textarea[name='description']", "What the hike is like: the route, the views, and what to bring.")
        snap("07-reuse-settings")
    finally:
        drush_php(site, '\\Drupal\\node\\Entity\\NodeType::load("hike_screenshot")?->delete();')


# name: (site, function, logged in, full page[, window width])
SHOTS = {
    "06-add-content-type": ("core", add_content_type, True, False),
    "06-add-field": ("core", add_field, True, False),
    "06-add-field-type": ("core", add_field_type, True, False),
    "06-add-field-settings": ("core", add_field_settings, True, False),
    "06-manage-fields": ("core", manage_fields, True, False),
    "06-content-form": ("core", content_form, True, False),
    "06-front-page-setting": ("core", front_page_setting, True, False),
    "06-front-page": ("core", visitor("/"), False, False),
    "06-revisions": ("core", revisions, True, False),
    "06-moderation-state": ("core", moderation_state, True, False),
    "08-layout-builder": ("core", layout_builder, True, False),
    "08-how-to-join": ("core", visitor("/join"), False, False),
    "08-canvas-editor": ("cms", canvas_editor, True, False, 1600),
    "08-canvas-how-to-join": ("cms", visitor("/join"), False, False),
    "06-trash": ("cms", trash, True, False),
    "07-add-hike": ("core", add_hike, True, False),
    "07-add-date": ("core", add_date, True, False),
    "07-date-settings": ("core", date_settings, True, False),
    "07-distance-settings": ("core", distance_settings, True, False),
    "07-difficulty-settings": ("core", difficulty_settings, True, False),
    "07-hike-leader-settings": ("core", hike_leader_settings, True, False),
    "07-hike-fields": ("core", hike_fields, True, False),
    "07-hike-form-display": ("core", hike_form_display, True, False),
    "07-hike-form": ("core", hike_form, True, False),
    "07-hike-page": ("core", visitor("/hikes/turnhouse-hill"), False, True),
    "07-hike-permissions": ("core", hike_permissions, True, False),
    "07-cms-utility-page-fields": ("cms", cms_utility_page_fields, True, False),
}


# Sequences: several screenshots from one run of steps.
# (site, function, window width, the names it takes)
SEQUENCES = [
    ("core", reuse_field_steps, 1280, ["07-reuse-field", "07-reuse-settings"]),
    ("core", layout_builder_steps, 1600, ["08-lb-start", "08-lb-choose-layout", "08-lb-column-widths", "08-lb-choose-block", "08-lb-content-block", "08-lb-body-block", "08-lb-remove-section", "08-lb-save"]),
    ("cms", canvas_steps, 1600, ["08-canvas-page-data", "08-canvas-heading", "08-canvas-grid", "08-canvas-text", "08-canvas-move", "08-canvas-card", "08-canvas-publish"]),
]


def matches(name: str, wanted: list[str]) -> bool:
    return not wanted or any(name == w or name.startswith(w + "-") for w in wanted)


def save(page: Page, name: str, full_page: bool = False) -> None:
    target = IMAGES / f"{name}.png"
    page.screenshot(path=str(target), full_page=full_page)
    subprocess.run(["sips", "--resampleWidth", str(WIDTH), str(target)], check=True, capture_output=True)
    print(f"{target.relative_to(ROOT)}")


def log_in(page: Page, site: dict) -> None:
    page.goto(site["url"] + "/user/login")
    page.fill("#edit-name", site["user"])
    page.fill("#edit-pass", site["password"])
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")


def main(wanted: list[str]) -> int:
    names = [n for n in SHOTS if matches(n, wanted)]
    sequences = [s for s in SEQUENCES if any(matches(n, wanted) for n in s[3])]
    if not names and not sequences:
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
            save(page, name, full_page)
            page.close()
        for site_name, steps, width, _ in sequences:
            site = SITES[site_name]
            context = browser.new_context(viewport={"width": width, "height": 1000}, device_scale_factor=2, ignore_https_errors=True)
            page = context.new_page()
            log_in(page, site)
            steps(page, site, lambda name: save(page, name))
            context.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
