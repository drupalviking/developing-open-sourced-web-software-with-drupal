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

import json
import os
import shutil
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
    # Chapter 20's Drupal 11 site, for a patch update and preparing the upgrade to Drupal 12.
    "d11": {
        "url": os.environ.get("D11_URL", "https://lens-and-trail-d11.ddev.site:8443"),
        "dir": os.environ.get("D11_DIR", str(Path.home() / "websites/open-university/lens-and-trail-d11")),
        "user": "admin",
        "password": "12345",
    },
    # Chapter 21's second copy of the club's core site, playing the live site: a clone of "core" (see config21_live).
    "live": {
        "url": os.environ.get("LIVE_URL", "https://lens-and-trail-live.ddev.site:8443"),
        "dir": os.environ.get("LIVE_DIR", str(Path.home() / "websites/open-university/lens-and-trail-live")),
        "user": "admin",
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


def cms_utility_page_display(page: Page, url: str) -> None:
    page.goto(url + "/admin/structure/types/manage/page/display/default")
    page.wait_for_load_state("networkidle")
    scroll_to(page, "table")


def cms_focal_point(page: Page, url: str) -> None:
    """Drupal CMS's Add Image form with a photo uploaded (not saved), to show Focal Point."""
    page.goto(url + "/media/add/image")
    page.set_input_files("input[type='file']", str(ROOT / "examples" / "photos" / "turnhouse-hill-glencorse.jpg"))
    page.wait_for_selector(".focal-point-indicator")
    page.wait_for_timeout(2000)
    scroll_to(page, ".focal-point-indicator", 250)


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
        # When the reader gets here, Body is the only field to re-use, and only
        # Basic page uses it; the finished site has more, so the window shows
        # only Body's row, used in Basic page.
        page.evaluate("""() => document.querySelectorAll('.ui-dialog tbody tr').forEach(r => {
            if (!r.textContent.includes('field_body')) { r.remove(); return; }
            r.querySelectorAll('td *').forEach(e => {
                if (e.children.length === 0 && e.textContent.trim().startsWith('Used in:')) e.textContent = 'Used in: Basic page';
            });
        })""")
        snap("07-reuse-field", ".ui-dialog")
        page.locator(".ui-dialog tr", has_text="field_body").locator("input, button").first.click()
        page.wait_for_url("**/node.hike_screenshot.field_body")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='label']", "Description")
        page.fill("textarea[name='description']", "What the hike is like: the route, the views, and what to bring.")
        snap("07-reuse-settings")
    finally:
        drush_php(site, '\\Drupal\\node\\Entity\\NodeType::load("hike_screenshot")?->delete();')



FIXTURES = ROOT / "tools" / "fixtures"


def restore_config(site: dict, name: str, folder: str = "") -> None:
    """Puts a configuration object back as it is in tools/fixtures/ (or a folder in it), keeping its UUID.

    tools/fixtures/ has the configuration as Chapter 7 leaves it; tools/fixtures/chapter-08/
    as Chapter 8 leaves it.
    """
    yaml = (FIXTURES / folder / f"{name}.yml").read_text()
    drush_php(site, f"""$y = <<<'YAML'
{yaml}
YAML;
$c = \\Drupal::configFactory()->getEditable('{name}');
$data = \\Drupal\\Component\\Serialization\\Yaml::decode($y);
$data['uuid'] = $c->get('uuid');
$c->setData($data)->save();""")


def reset_displays(site: dict) -> None:
    """Hike's and News's displays as Chapter 7 leaves them: Default only, no Card, no new date format."""
    drush_php(site, """$s = \\Drupal::entityTypeManager()->getStorage('entity_view_display');
foreach (['node.hike.teaser', 'node.hike.card', 'node.news.teaser', 'node.news.card'] as $id) { $s->load($id)?->delete(); }
\\Drupal::entityTypeManager()->getStorage('entity_view_mode')->load('node.card')?->delete();
\\Drupal::entityTypeManager()->getStorage('date_format')->load('day_date_and_time')?->delete();""")
    for name in ("core.entity_view_display.node.hike.default", "core.entity_view_display.node.news.default"):
        restore_config(site, name)
    subprocess.run(["ddev", "drush", "cache:rebuild"], cwd=site["dir"], check=True, capture_output=True)


def as_visitor(page: Page, site: dict, path: str, name: str, width: int = WIDTH, prepare=None) -> None:
    """A full-page screenshot of path, logged out, in a window of its own. prepare(page) runs before it's taken."""
    context = page.context.browser.new_context(viewport={"width": width, "height": 1000}, device_scale_factor=2, ignore_https_errors=True)
    visit = context.new_page()
    visit.goto(site["url"] + path)
    visit.wait_for_load_state("networkidle")
    if prepare:
        prepare(visit)
    save(visit, name, full_page=True)
    context.close()


def drag_row(page: Page, row: str, below: str) -> None:
    """Drags a table row by its handle until it is below another row."""
    handle = page.locator(f"tr:has-text('{row}') .tabledrag-handle").first.bounding_box()
    target = page.locator(f"tr:has-text('{below}')").first.bounding_box()
    x, y = handle["x"] + handle["width"] / 2, handle["y"] + handle["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x, target["y"] + target["height"] - 5, steps=25)
    page.mouse.up()
    page.wait_for_timeout(1000)


def set_label(page: Page, field: str, label: str) -> None:
    select = f"select[name='fields[{field}][label]']"
    page.select_option(select, label)
    page.wait_for_timeout(800)
    if page.input_value(select) != label:
        raise RuntimeError(f"{field}'s label didn't change to {label}")


def field_settings(page: Page, field: str) -> str:
    """Opens a field's formatter settings (the cog) and returns the prefix of their form names."""
    page.click(f"input[name='{field}_settings_edit']")
    page.wait_for_selector(f"input[name='{field}_plugin_settings_update']")
    page.wait_for_timeout(1000)
    return f"fields[{field}][settings_edit_form][settings]"


def field_settings_update(page: Page, field: str) -> None:
    page.click(f"input[name='{field}_plugin_settings_update']")
    page.wait_for_selector(f"input[name='{field}_settings_edit']")
    page.wait_for_timeout(1000)


def disable_fields(page: Page, fields: list[str]) -> None:
    """Moves fields to the Disabled region, through the Region selects behind Show row weights."""
    row_weights(page, True)
    for field in fields:
        page.select_option(f"select[name='fields[{field}][region]']", "hidden")
        page.wait_for_timeout(800)
    row_weights(page, False)
    page.wait_for_timeout(500)


def save_display(page: Page) -> None:
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")


def manage_display_steps(page: Page, site: dict, snap) -> None:
    """Chapter 8's Manage display steps, from the displays Chapter 7 leaves.

    Resets Hike's and News's displays first, and leaves them as Chapter 8 does
    (the News Try it is done with drush, without screenshots).
    """
    url = site["url"]
    reset_displays(site)
    as_visitor(page, site, "/hikes/turnhouse-hill", "08-hike-before")
    display = url + "/admin/structure/types/manage/hike/display"

    page.goto(display)
    snap("08-display-overview")
    page.goto(display + "/default")
    page.wait_for_load_state("networkidle")
    scroll_to(page, "table")
    snap("08-display-default")

    drag_row(page, "field_body", "field_hike_leader")
    scroll_to(page, "table")
    snap("08-display-order")

    for field in ("field_date", "field_meeting_place", "field_distance", "field_difficulty", "field_hike_leader"):
        set_label(page, field, "inline")
    scroll_to(page, "table")
    snap("08-display-labels")

    prefix = field_settings(page, "field_distance")
    page.fill(f"input[name='{prefix}[scale]']", "1")
    scroll_to(page, "tr:has-text('field_distance')", 200)
    snap("08-display-distance")
    field_settings_update(page, "field_distance")

    prefix = field_settings(page, "field_hike_leader")
    page.uncheck(f"input[name='{prefix}[link]']")
    scroll_to(page, "tr:has-text('field_hike_leader')", 300)
    snap("08-display-hike-leader")
    field_settings_update(page, "field_hike_leader")
    save_display(page)

    page.goto(url + "/admin/config/regional/date-time/formats/add")
    page.fill("input[name='label']", "Day, date and time")
    page.wait_for_timeout(1500)
    page.fill("input[name='date_format_pattern']", "l, j F Y \\a\\t H:i")
    page.locator("input[name='date_format_pattern']").evaluate("e => e.blur()")
    page.wait_for_timeout(2500)
    snap("08-date-format")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    page.goto(display + "/default")
    prefix = field_settings(page, "field_date")
    page.select_option(f"select[name='{prefix}[format_type]']", "day_date_and_time")
    page.wait_for_timeout(500)
    scroll_to(page, "tr:has-text('field_date')", 200)
    snap("08-display-date")
    field_settings_update(page, "field_date")
    save_display(page)
    as_visitor(page, site, "/hikes/turnhouse-hill", "08-hike-after")

    # Teaser: for lists of hikes (Chapter 12).
    page.goto(display)
    page.click("tr:has-text('Teaser') a:has-text('Enable')")
    page.wait_for_load_state("networkidle")
    page.goto(display + "/teaser")
    page.wait_for_load_state("networkidle")
    disable_fields(page, ["field_meeting_place", "field_hike_leader"])
    drag_row(page, "field_body", "field_difficulty")
    for field in ("field_date", "field_distance", "field_difficulty"):
        set_label(page, field, "inline")
    page.select_option("select[name='fields[field_body][type]']", "text_trimmed")
    page.wait_for_selector("input[name='field_body_settings_edit']")
    page.wait_for_timeout(1500)
    prefix = field_settings(page, "field_body")
    page.fill(f"input[name='{prefix}[trim_length]']", "200")
    field_settings_update(page, "field_body")
    prefix = field_settings(page, "field_date")
    page.select_option(f"select[name='{prefix}[format_type]']", "day_date_and_time")
    field_settings_update(page, "field_date")
    scroll_to(page, "table")
    snap("08-display-teaser")
    save_display(page)

    # Card: a view mode of our own.
    page.goto(url + "/admin/structure/display-modes/view/add/node")
    page.fill("input[name='label']", "Card")
    page.wait_for_timeout(1500)
    page.fill("textarea[name='description'], input[name='description']", "A small box with the date and the difficulty, for the front page.")
    page.check("input[name='bundles_by_entity[hike]']")
    snap("08-view-mode-add")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    page.goto(display + "/card")
    page.wait_for_load_state("networkidle")
    disable_fields(page, ["field_body", "field_meeting_place", "field_distance", "field_hike_leader", "links"])
    for field in ("field_date", "field_difficulty"):
        set_label(page, field, "hidden")
    prefix = field_settings(page, "field_date")
    page.select_option(f"select[name='{prefix}[format_type]']", "day_date_and_time")
    field_settings_update(page, "field_date")
    scroll_to(page, "table")
    snap("08-display-card")
    save_display(page)

    # The News Try it.
    drush_php(site, """$d = \\Drupal::service('entity_display.repository')->getViewDisplay('node', 'news', 'teaser');
$d->setComponent('field_body', ['type' => 'text_trimmed', 'label' => 'hidden', 'settings' => ['trim_length' => 300], 'weight' => 101])->save();""")


HIKE_LAYOUT = r"""
use Drupal\layout_builder\Section;
use Drupal\layout_builder\SectionComponent;
$storage = \Drupal::entityTypeManager()->getStorage('entity_view_display');
$storage->load('node.hike.full')?->delete();
$display = $storage->load('node.hike.default')->createCopy('full');
$display->setStatus(TRUE)->save();
$display = $storage->load('node.hike.full');
$display->enableLayoutBuilder()->save();
$section = new Section('layout_twocol_section', ['label' => '', 'column_widths' => '67-33']);
$uuid = \Drupal::service('uuid');
$block = fn ($field, $label, $formatter) => [
  'id' => "field_block:node:hike:$field",
  'label' => $field,
  'label_display' => '0',
  'provider' => 'layout_builder',
  'context_mapping' => ['entity' => 'layout_builder.entity', 'view_mode' => 'view_mode'],
  'formatter' => $formatter + ['label' => $label, 'third_party_settings' => []],
];
$section->appendComponent(new SectionComponent($uuid->generate(), 'first', $block('field_body', 'hidden', ['type' => 'text_default', 'settings' => []])));
$facts = [
  'field_date' => ['type' => 'datetime_default', 'settings' => ['format_type' => 'day_date_and_time', 'timezone_override' => '']],
  'field_meeting_place' => ['type' => 'string', 'settings' => ['link_to_entity' => FALSE]],
  'field_distance' => ['type' => 'number_decimal', 'settings' => ['thousand_separator' => '', 'decimal_separator' => '.', 'scale' => 1, 'prefix_suffix' => TRUE]],
  'field_difficulty' => ['type' => 'list_default', 'settings' => []],
  'field_hike_leader' => ['type' => 'entity_reference_label', 'settings' => ['link' => FALSE]],
];
$weight = 0;
foreach ($facts as $field => $formatter) {
  $section->appendComponent((new SectionComponent($uuid->generate(), 'second', $block($field, 'above', $formatter)))->setWeight($weight++));
}
$display->removeAllSections()->appendSection($section)->save();
"""


def hike_layout_exercise(page: Page, site: dict, snap) -> None:
    """Chapter 8's Layout Builder exercise: the hike on Full content, with the facts on the side.

    Uses the Full content view mode, so Hike's Default display is untouched, and
    deletes it afterwards (the page falls back to Default).
    """
    drush_php(site, HIKE_LAYOUT)
    try:
        as_visitor(page, site, "/hikes/turnhouse-hill", "08-exercise-hike-layout")
    finally:
        drush_php(site, "\\Drupal::entityTypeManager()->getStorage('entity_view_display')->load('node.hike.full')?->delete();")


# Chapter 9: media. The parts run in order; each one undoes its own changes
# first, so a part can be retaken on its own once the parts before it have run.

PHOTOS = ROOT / "examples" / "photos"
TURNHOUSE_ALT = "Turnhouse Hill seen across Glencorse Reservoir, with a rowing boat at the landing stage"


def uninstall(site: dict, *modules: str) -> None:
    enabled = drush_php(site, "echo implode(' ', array_keys(\\Drupal::moduleHandler()->getModuleList()));").split()
    modules = [m for m in modules if m in enabled]
    if modules:
        subprocess.run(["ddev", "drush", "pm:uninstall", "-y", *modules], cwd=site["dir"], check=True, capture_output=True)


def delete_fields(site: dict, entity_type: str, *names: str) -> None:
    names_php = ", ".join(f"'{n}'" for n in names)
    drush_php(site, f"foreach ([{names_php}] as $n) {{ \\Drupal\\field\\Entity\\FieldStorageConfig::loadByName('{entity_type}', $n)?->delete(); }} field_purge_batch(500);")


def create_field(page: Page, fields_url: str, group: str, label: str, choice: str | None, settings=None, shot=None) -> None:
    """Creates a field through the Add field window, and saves it."""
    page.goto(fields_url)
    page.click("text=Create a new field")
    page.wait_for_selector(".ui-dialog")
    page.wait_for_timeout(1500)
    page.locator(".ui-dialog").get_by_text(group, exact=True).first.click()
    page.wait_for_timeout(1500)
    page.fill(".ui-dialog input[name='label']", label)
    page.wait_for_timeout(1500)
    if choice:
        page.click(f".ui-dialog label:has-text('{choice}')")
    if shot:
        shot("type")
    page.click(".ui-dialog button:has-text('Continue')")
    page.wait_for_selector(".ui-dialog-title:has-text('settings')")
    page.wait_for_timeout(1500)
    if settings:
        settings(page)
    if shot:
        shot("settings")
    page.click(".ui-dialog-buttonpane button:has-text('Save')")
    page.wait_for_selector(".ui-dialog", state="detached")
    page.wait_for_load_state("networkidle")


def row_weights(page: Page, show: bool) -> None:
    """Shows or hides the row weights. Drupal remembers the choice in the browser, so check first."""
    button = page.locator("button:has-text('Show row weights')" if show else "button:has-text('Hide row weights')")
    if button.count() and button.first.is_visible():
        button.first.click()
        page.wait_for_timeout(500)


def set_weights(page: Page, weights: dict[str, int]) -> None:
    """Sets rows' weights through Show row weights (the lower, the higher up)."""
    row_weights(page, True)
    for field, weight in weights.items():
        box = page.locator(f"[name='fields[{field}][weight]']")
        if box.evaluate("e => e.tagName") == "SELECT":
            box.select_option(str(weight))
        else:
            box.fill(str(weight))
            box.dispatch_event("change")
        page.wait_for_timeout(500)
    row_weights(page, False)
    page.wait_for_timeout(500)


def form_regions(page: Page, url: str, fields: list[str], region: str = "content") -> None:
    """Moves fields in or out of a form or display, through the Region selects, and saves."""
    page.goto(url)
    page.wait_for_load_state("networkidle")
    row_weights(page, True)
    for field in fields:
        page.select_option(f"select[name='fields[{field}][region]']", region)
        page.wait_for_timeout(800)
    row_weights(page, False)
    page.wait_for_timeout(500)


def media_install_steps(page: Page, site: dict, snap) -> None:
    """Chapter 9, part 1: Media, the Image media type's credit fields, and the first photo."""
    url = site["url"]
    drush_php(site, """if (\\Drupal::moduleHandler()->moduleExists('media')) {
  foreach (['gallery'] as $t) { $s = \\Drupal::entityTypeManager()->getStorage('node'); $s->delete($s->loadByProperties(['type' => $t])); \\Drupal\\node\\Entity\\NodeType::load($t)?->delete(); }
  $s = \\Drupal::entityTypeManager()->getStorage('media'); $s->delete($s->loadMultiple());
}""")
    delete_fields(site, "node", "field_photo", "field_photos", "field_hike")
    uninstall(site, "responsive_image", "media_library", "media")
    drush_php(site, """$s = \\Drupal::entityTypeManager()->getStorage('file');
foreach ($s->loadMultiple() as $f) { if (str_starts_with($f->getFileUri(), 'public://20')) { $f->delete(); } }
foreach (['banner', 'banner_small', 'banner_large', 'black_and_white', 'square'] as $id) { \\Drupal\\image\\Entity\\ImageStyle::load($id)?->delete(); }""")
    for name in ("editor.editor.basic_html", "filter.format.basic_html"):
        restore_config(site, name)
    subprocess.run(["ddev", "drush", "cache:rebuild"], cwd=site["dir"], check=True, capture_output=True)

    page.goto(url + "/admin/modules")
    page.fill("input[name='text']", "media")
    page.wait_for_timeout(1000)
    page.check("input[name='modules[media][enable]']")
    page.check("input[name='modules[media_library][enable]']")
    scroll_to(page, "tr:has(input[name='modules[media][enable]'])", 300)
    snap("09-extend-media")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    page.goto(url + "/admin/structure/media")
    snap("09-media-types")

    fields = url + "/admin/structure/media/manage/image/fields"
    create_field(page, fields, "Plain text", "Photographer", "Short text",
                 lambda p: dialog_fill(p, "description", "The photographer's name, as they want to be credited."))

    def license_settings(p: Page) -> None:
        for i, name in enumerate(["CC BY-SA 4.0", "CC BY-SA 2.0", "CC BY 4.0", "CC0", "All rights reserved, used with permission"]):
            if i:
                p.click(".ui-dialog input[name='add_more_allowed_values']")
                p.wait_for_timeout(2500)
            dialog_fill(p, f"field_storage[subform][settings][allowed_values][table][{i}][item][label]", name)
        dialog_fill(p, "description", "The license the photo is published under. Use only photos you're allowed to publish.")
        p.check(".ui-dialog input[name='required']")
        dialog_scroll_to(p, "[name='field_storage[subform][settings][allowed_values][table][0][item][label]']")

    create_field(page, fields, "Selection list", "License", "Text", license_settings,
                 lambda step: snap("09-license-settings", ".ui-dialog") if step == "settings" else None)

    def source_settings(p: Page) -> None:
        p.check(".ui-dialog input[name='settings[link_type]'][value='16']")
        p.check(".ui-dialog input[name='settings[title]'][value='1']")
        dialog_fill(p, "description", "Where the photo comes from, such as its page on Wikimedia Commons.")

    create_field(page, fields, "Link", "Source", None, source_settings)
    page.goto(fields)
    snap("09-image-fields")

    for mode in ("default", "media_library"):
        form_regions(page, f"{url}/admin/structure/media/manage/image/form-display/{mode}", ["name", "field_photographer", "field_license", "field_source"])
        set_weights(page, {"field_media_image": 0, "name": 1, "field_photographer": 2, "field_license": 3, "field_source": 4})
        page.click("#edit-submit")
        page.wait_for_load_state("networkidle")
        if mode == "media_library":
            row_weights(page, False)
            scroll_to(page, "table")
            snap("09-image-form-media-library")

    page.goto(url + "/media/add/image")
    page.set_input_files("input[type='file']", str(PHOTOS / "turnhouse-hill-glencorse.jpg"))
    page.wait_for_selector("input[name='field_media_image[0][alt]']")
    page.wait_for_timeout(1500)
    page.fill("input[name='name[0][value]']", "Turnhouse Hill across Glencorse Reservoir")
    page.fill("input[name='field_media_image[0][alt]']", TURNHOUSE_ALT)
    page.fill("input[name='field_photographer[0][value]']", "dave souza")
    page.select_option("select[name='field_license']", label="CC BY-SA 4.0")
    page.fill("input[name='field_source[0][uri]']", "https://commons.wikimedia.org/wiki/File:Glencorse_Reservoir,_Turnhouse_Hill.jpg")
    page.fill("input[name='field_source[0][title]']", "Wikimedia Commons")
    page.set_viewport_size({"width": WIDTH, "height": 1450})
    page.wait_for_timeout(800)
    snap("09-add-image")
    page.set_viewport_size({"width": WIDTH, "height": 1000})
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    page.goto(url + "/admin/content/media")
    snap("09-media-list")


def photo_field_steps(page: Page, site: dict, snap) -> None:
    """Chapter 9, part 2: a Photo field on Hike, and the photo on the first hike."""
    url = site["url"]
    delete_fields(site, "node", "field_photo")
    restore_config(site, "core.entity_view_display.node.hike.default", "chapter-08")
    subprocess.run(["ddev", "drush", "cache:rebuild"], cwd=site["dir"], check=True, capture_output=True)

    def photo_settings(p: Page) -> None:
        p.check(".ui-dialog input[name='settings[handler_settings][target_bundles][image]']")
        p.wait_for_timeout(2000)
        dialog_fill(p, "description", "A photo of the hike's area, shown at the top of the hike.")
        dialog_scroll_to(p, "[name='settings[handler_settings][target_bundles][image]']")

    create_field(page, url + "/admin/structure/types/manage/hike/fields", "Media", "Photo", None, photo_settings,
                 lambda step: snap("09-photo-field-type" if step == "type" else "09-photo-field-settings", ".ui-dialog"))

    page.goto(url + "/node/7/edit")
    page.wait_for_load_state("networkidle")
    page.click("input[name='field_photo-media-library-open-button']")
    page.wait_for_selector(".media-library-widget-modal .js-media-library-item")
    page.wait_for_timeout(2000)
    page.locator(".media-library-widget-modal .js-media-library-item").first.locator("input[type='checkbox']").check()
    page.wait_for_timeout(800)
    snap("09-media-library", ".ui-dialog")
    page.click(".ui-dialog-buttonpane button:has-text('Insert selected')")
    page.wait_for_selector(".ui-dialog", state="detached")
    page.wait_for_timeout(2000)
    page.select_option("select[name='moderation_state[0][state]']", "published")
    scroll_to(page, "#field_photo-media-library-wrapper, [id^='field_photo-media-library-wrapper']", 200)
    snap("09-hike-form-photo")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    display = url + "/admin/structure/types/manage/hike/display/default"
    page.goto(display)
    page.wait_for_load_state("networkidle")
    set_label(page, "field_photo", "hidden")
    set_weights(page, {"field_photo": -10})
    save_display(page)
    as_visitor(page, site, "/hikes/turnhouse-hill", "09-hike-photo-large")


def add_image_style(page: Page, url: str, label: str, effects: list, shot=None) -> None:
    """Creates an image style with its effects: (effect id, {field: value}), in order."""
    page.goto(url + "/admin/config/media/image-styles/add")
    page.fill("input[name='label']", label)
    page.wait_for_timeout(1500)
    page.click("input[value='Create new style']")
    page.wait_for_load_state("networkidle")
    for effect, values in effects:
        page.select_option("select[name='new']", effect)
        page.click("input[value='Add']")
        page.wait_for_load_state("networkidle")
        if values:
            for name, value in values.items():
                box = page.locator(f"[name='{name}']")
                if box.evaluate("e => e.tagName") == "SELECT":
                    box.select_option(value)
                else:
                    box.fill(value)
            page.click("#edit-submit")
            page.wait_for_load_state("networkidle")
    if shot:
        shot()
    page.click("form#image-style-edit-form input[value='Save']")
    page.wait_for_load_state("networkidle")


BANNER_SIZES = "(min-width: 1130px) 905px, 100vw"


def image_styles_steps(page: Page, site: dict, snap) -> None:
    """Chapter 9, part 3: image styles, the Banner view mode for media, and responsive images."""
    url = site["url"]
    drush_php(site, """foreach (['banner', 'banner_small', 'banner_large', 'black_and_white'] as $id) { \\Drupal\\image\\Entity\\ImageStyle::load($id)?->delete(); }
if (\\Drupal::moduleHandler()->moduleExists('responsive_image')) { foreach (\\Drupal::entityTypeManager()->getStorage('responsive_image_style')->loadMultiple() as $r) { $r->delete(); } }
\\Drupal::entityTypeManager()->getStorage('entity_view_display')->load('media.image.banner')?->delete();
\\Drupal::entityTypeManager()->getStorage('entity_view_mode')->load('media.banner')?->delete();
$d = \\Drupal::entityTypeManager()->getStorage('entity_view_display')->load('node.hike.default');
$c = $d->getComponent('field_photo'); $c['settings']['view_mode'] = 'default'; $d->setComponent('field_photo', $c)->save();""")
    uninstall(site, "responsive_image")
    subprocess.run(["ddev", "drush", "cache:rebuild"], cwd=site["dir"], check=True, capture_output=True)

    page.goto(url + "/admin/config/media/image-styles")
    snap("09-image-styles")

    def banner_shot() -> None:
        page.set_viewport_size({"width": WIDTH, "height": 1300})
        page.wait_for_timeout(800)
        snap("09-image-style-banner")
        page.set_viewport_size({"width": WIDTH, "height": 1000})

    add_image_style(page, url, "Banner", [
        ("image_scale_and_crop", {"data[width]": "1280", "data[height]": "720"}),
        ("image_convert_avif", {"data[extension]": "webp"}),
    ], banner_shot)

    page.goto(url + "/admin/structure/display-modes/view/add/media")
    page.fill("input[name='label']", "Banner")
    page.wait_for_timeout(1500)
    page.fill("textarea[name='description'], input[name='description']", "A wide photo with its credits, at the top of a page.")
    page.check("input[name='bundles_by_entity[image]']")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    page.goto(url + "/admin/structure/media/manage/image/display/banner")
    page.wait_for_load_state("networkidle")
    set_label(page, "field_media_image", "hidden")
    prefix = field_settings(page, "field_media_image")
    page.select_option(f"select[name='{prefix}[image_style]']", "banner")
    field_settings_update(page, "field_media_image")
    for field in ("field_photographer", "field_license", "field_source"):
        set_label(page, field, "inline")
    row_weights(page, False)
    scroll_to(page, "table")
    snap("09-media-banner-display")
    save_display(page)

    page.goto(url + "/admin/structure/types/manage/hike/display/default")
    page.wait_for_load_state("networkidle")
    prefix = field_settings(page, "field_photo")
    page.select_option(f"select[name='{prefix}[view_mode]']", "banner")
    scroll_to(page, "tr:has-text('field_photo')", 200)
    snap("09-hike-photo-view-mode")
    field_settings_update(page, "field_photo")
    save_display(page)
    as_visitor(page, site, "/hikes/turnhouse-hill", "09-hike-banner")

    # Responsive images.
    for label, width, height in (("Banner small", "640", "360"), ("Banner large", "1920", "1080")):
        add_image_style(page, url, label, [
            ("image_scale_and_crop", {"data[width]": width, "data[height]": height}),
            ("image_convert_avif", {"data[extension]": "webp"}),
        ])
    page.goto(url + "/admin/modules")
    page.fill("input[name='text']", "responsive")
    page.wait_for_timeout(1000)
    page.check("input[name='modules[responsive_image][enable]']")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    page.goto(url + "/admin/config/media/responsive-image-style/add")
    page.fill("input[name='label']", "Banner")
    page.wait_for_timeout(1500)
    page.select_option("select[name='breakpoint_group']", "responsive_image")
    page.wait_for_timeout(2500)
    page.click("summary:has-text('1x Viewport Sizing')")
    page.wait_for_timeout(800)
    page.check("input[type='radio'][value='sizes']")
    page.wait_for_timeout(1000)
    page.fill("textarea[name$='[sizes]']", BANNER_SIZES)
    for style in ("banner_small", "banner", "banner_large"):
        page.check(f"input[name$='[sizes_image_styles][{style}]']")
    page.select_option("select[name='fallback_image_style']", "banner")
    page.set_viewport_size({"width": WIDTH, "height": 1500})
    page.wait_for_timeout(800)
    snap("09-responsive-style")
    page.set_viewport_size({"width": WIDTH, "height": 1000})
    page.click("main input[value='Save']")
    page.wait_for_load_state("networkidle")

    page.goto(url + "/admin/structure/media/manage/image/display/banner")
    page.wait_for_load_state("networkidle")
    page.select_option("select[name='fields[field_media_image][type]']", "responsive_image")
    page.wait_for_selector("input[name='field_media_image_settings_edit']")
    page.wait_for_timeout(1500)
    prefix = field_settings(page, "field_media_image")
    page.select_option(f"select[name='{prefix}[responsive_image_style]']", "banner")
    scroll_to(page, "tr:has-text('field_media_image')", 200)
    snap("09-media-banner-responsive")
    field_settings_update(page, "field_media_image")
    save_display(page)

    context = page.context.browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, ignore_https_errors=True)
    phone = context.new_page()
    phone.goto(url + "/hikes/turnhouse-hill")
    phone.wait_for_load_state("networkidle")
    target = IMAGES / "09-hike-phone.png"
    phone.screenshot(path=str(target))
    subprocess.run(["sips", "--resampleWidth", "780", str(target)], check=True, capture_output=True)
    print(target.relative_to(ROOT), phone.evaluate("document.querySelector('.field--name-field-photo img').currentSrc"))
    context.close()


# What later chapters add to Hike's form and display: Area (10), Simple XML Sitemap and URL redirects (17),
# Language (18), Elevation gain (21).
LATER_ROWS = ["field-area", "simple-sitemap", "url-redirects", "langcode", "field-elevation-gain"]
# What later chapters add to the hike page: the logo and green colour (16), the Hikes and Albums menu links,
# the breadcrumb's Upcoming hikes, the sidebar and the footer's blocks (14), Albums from this hike (13),
# the language switcher (18), and Area (10).
LATER_PAGE = [
    ".site-branding__logo", "#block-olivero-languageswitcher", ".region--sidebar", ".region--footer-top",
    "#block-olivero-footer", "#block-olivero-albums-from-this-hike", ".field--name-field-area",
]


def hide_later(page: Page, rows: list[str] = (), elements: list[str] = ()) -> None:
    """Takes out of the page what later chapters add, so a screenshot taken now looks like an earlier chapter's.

    rows are table row ids (Manage form display, Manage display); elements are CSS selectors on a visitor page.
    """
    page.evaluate("""([rows, elements]) => {
        rows.forEach(id => document.getElementById(id)?.remove());
        elements.forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
        if (elements.length) {
            document.documentElement.removeAttribute('style');
            document.querySelectorAll('.primary-nav__menu-item--level-1').forEach(li => {
                if (!['Home', 'About', 'Join us'].includes(li.querySelector('a, button')?.innerText.trim())) li.remove();
            });
            document.querySelectorAll('.breadcrumb__item').forEach((li, i) => { if (i > 0) li.remove(); });
        }
    }""", [list(rows), list(elements)])
    page.wait_for_timeout(300)


def widgets_formatters_steps(page: Page, site: dict, snap) -> None:
    """Chapter 9: the Media library widget, and Thumbnail compared with Rendered entity.

    Only looks at the site as it is (any chapter from 9 on), taking out what later chapters add
    (hide_later): the Thumbnail steps save Hike's display, and the display is put back as it was afterwards.
    """
    url = site["url"]
    page.goto(url + "/admin/structure/types/manage/hike/form-display")
    page.wait_for_load_state("networkidle")
    hide_later(page, LATER_ROWS)
    scroll_to(page, "tr:has-text('field_photo')", 250)
    snap("09-photo-widget")

    backup = drush_php(site, "echo json_encode(\\Drupal::entityTypeManager()->getStorage('entity_view_display')->load('node.hike.default')->getComponent('field_photo'));")
    component = json.loads(backup.strip().splitlines()[-1])
    try:
        display = url + "/admin/structure/types/manage/hike/display/default"
        page.goto(display)
        page.wait_for_load_state("networkidle")
        select = "select[name='fields[field_photo][type]']"
        # A screenshot can't show a native drop-down open, so show the select as a list.
        page.evaluate(f"""() => {{ const s = document.querySelector("{select}"); s.size = s.options.length; s.style.height = 'auto'; }}""")
        hide_later(page, LATER_ROWS)
        scroll_to(page, "tr:has-text('field_photo')", 250)
        page.wait_for_timeout(500)
        snap("09-photo-formatters")
        page.reload()
        page.wait_for_load_state("networkidle")

        page.select_option(select, "media_thumbnail")
        page.wait_for_selector("input[name='field_photo_settings_edit']")
        page.wait_for_timeout(1500)
        prefix = field_settings(page, "field_photo")
        page.select_option(f"select[name='{prefix}[image_style]']", "large")
        page.select_option(f"select[name='{prefix}[image_link]']", "")
        hide_later(page, LATER_ROWS)
        scroll_to(page, "tr:has-text('field_photo')", 150)
        snap("09-photo-thumbnail-settings")
        field_settings_update(page, "field_photo")
        save_display(page)
        as_visitor(page, site, "/hikes/turnhouse-hill", "09-hike-thumbnail", prepare=lambda p: hide_later(p, elements=LATER_PAGE))
    finally:
        drush_php(site, f"""$d = \\Drupal::entityTypeManager()->getStorage('entity_view_display')->load('node.hike.default');
$d->setComponent('field_photo', json_decode('{json.dumps(component)}', TRUE))->save();""")
        subprocess.run(["ddev", "drush", "cache:rebuild"], cwd=site["dir"], check=True, capture_output=True)


# The gallery's photos, from examples/photos/CREDITS.md: file, name, alternative text, photographer, license, source.
ALBUM = [
    ("carnethy-from-turnhouse.jpg", "Carnethy Hill from Turnhouse Hill", "The path down from Turnhouse Hill, with Carnethy Hill rising behind it", "Jim Barton", "CC BY-SA 2.0", "https://commons.wikimedia.org/wiki/File:Carnethy_Hill_from_Turnhouse_Hill_-_geograph.org.uk_-_6273248.jpg"),
    ("carnethy-hill-views.jpg", "The view from Carnethy Hill", "Rolling green hills under a cloudy sky, seen from the stony top of Carnethy Hill", "Alan O'Dowd", "CC BY-SA 2.0", "https://commons.wikimedia.org/wiki/File:Carnethy_Hill_views_-_geograph.org.uk_-_4185120.jpg"),
    ("glencorse-reservoir-portrait.jpg", "Glencorse Reservoir from the hillside", "Glencorse Reservoir between the hills, seen from a grassy slope with two trees", "Jaroslaw Musialkowski", "CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Pentland_Hills_-_Glencorse_Reservoir.jpg"),
    ("pentland-hills-winter.jpg", "A burn in the Pentland Hills in winter", "A stream running through a snowy valley in the Pentland Hills", "Bops92", "CC BY-SA 4.0", "https://commons.wikimedia.org/wiki/File:Pentland_hills_winter.jpg"),
]
EDINBURGH = ("edinburgh-skyline.jpg", "Edinburgh's Old Town from Calton Hill", "Edinburgh's Old Town and the castle seen from Calton Hill, with trees in front", "Jim Barton", "CC BY-SA 2.0", "https://commons.wikimedia.org/wiki/File:Edinburgh_skyline_from_Calton_Hill_-_geograph.org.uk_-_7467002.jpg")


def library_fill(page: Page, photos: list) -> None:
    """Fills in the Media Library's form for freshly uploaded photos, in upload order."""
    for i, (_, name, alt, photographer, license, source) in enumerate(photos):
        prefix = f"media[{i}][fields]"
        page.fill(f".ui-dialog input[name='{prefix}[field_media_image][0][alt]']", alt)
        page.fill(f".ui-dialog input[name='{prefix}[name][0][value]']", name)
        page.fill(f".ui-dialog input[name='{prefix}[field_photographer][0][value]']", photographer)
        page.select_option(f".ui-dialog select[name='{prefix}[field_license]']", label=license)
        page.fill(f".ui-dialog input[name='{prefix}[field_source][0][uri]']", source)
        page.fill(f".ui-dialog input[name='{prefix}[field_source][0][title]']", "Wikimedia Commons")


def library_upload(page: Page, photos: list, shot=None) -> None:
    """In an open Media Library window: uploads photos, fills in their credits, and inserts them."""
    page.set_input_files(".ui-dialog input[type='file']", [str(PHOTOS / f[0]) for f in photos])
    page.wait_for_selector(".ui-dialog input[name='media[0][fields][field_media_image][0][alt]']")
    page.wait_for_timeout(2000)
    library_fill(page, photos)
    if shot:
        shot()
    page.click(".ui-dialog-buttonpane button:has-text('Save')")
    page.wait_for_selector(".ui-dialog-buttonpane button:has-text('Insert selected')")
    page.wait_for_timeout(1500)
    page.click(".ui-dialog-buttonpane button:has-text('Insert selected')")
    page.wait_for_selector(".ui-dialog", state="detached")
    page.wait_for_timeout(2000)


def media_editor_steps(page: Page, site: dict, snap) -> None:
    """Chapter 9, part 4: Photo on News (the Try it), and media in the text editor."""
    url = site["url"]
    drush_php(site, "\\Drupal\\field\\Entity\\FieldConfig::loadByName('node', 'news', 'field_photo')?->delete();")
    for name in ("editor.editor.basic_html", "filter.format.basic_html"):
        restore_config(site, name)
    drush_php(site, """$s = \\Drupal::entityTypeManager()->getStorage('media'); $s->delete($s->loadByProperties(['name' => 'Edinburgh\\'s Old Town from Calton Hill']));""")
    subprocess.run(["ddev", "drush", "cache:rebuild"], cwd=site["dir"], check=True, capture_output=True)
    page.goto(url + "/admin/structure/types/manage/news/fields")
    page.click("text=Re-use an existing field")
    page.wait_for_selector(".ui-dialog")
    page.wait_for_timeout(2000)
    page.locator(".ui-dialog tr", has_text="field_photo").locator("input, button").first.click()
    page.wait_for_url("**/node.news.field_photo")
    page.wait_for_load_state("networkidle")
    page.click("input[value='Save settings']")
    page.wait_for_url("**/news/fields")
    page.wait_for_load_state("networkidle")

    page.goto(url + "/node/8/edit")
    page.wait_for_load_state("networkidle")
    page.click("input[name='field_photo-media-library-open-button']")
    page.wait_for_selector(".ui-dialog input[type='file']")
    page.wait_for_timeout(1500)
    library_upload(page, [EDINBURGH], lambda: snap("09-library-upload", ".ui-dialog"))
    page.select_option("select[name='moderation_state[0][state]']", "published")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    page.goto(url + "/admin/config/content/formats/manage/basic_html")
    page.wait_for_load_state("networkidle")
    # Out with Upload image (pictures that aren't media), in with Drupal Media, in its place.
    page.locator(".ckeditor5-toolbar-active__buttons li[data-id='drupalInsertImage']").focus()
    page.keyboard.press("ArrowUp")
    page.wait_for_timeout(2000)
    page.locator(".ckeditor5-toolbar-available__buttons li[data-id='drupalMedia']").focus()
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(2000)
    media = page.locator(".ckeditor5-toolbar-active__buttons li[data-id='drupalMedia']")
    for _ in range(5):
        media.focus()
        page.keyboard.press("ArrowLeft")
        page.wait_for_timeout(500)
    page.check("input[name='filters[media_embed][status]']")
    page.wait_for_timeout(2000)
    page.click("a:has-text('Embed media')")
    page.wait_for_timeout(800)
    page.check("input[name='filters[media_embed][settings][allowed_media_types][image]']")
    page.select_option("select[name='filters[media_embed][settings][default_view_mode]']", "banner")
    scroll_to(page, ".ckeditor5-toolbar-configuration, [data-drupal-selector='edit-editor-settings-toolbar']", 150)
    snap("09-text-format-media")
    page.click("input[value='Save configuration']")
    page.wait_for_load_state("networkidle")

    # Only shown, not saved: an image inside the news item's text.
    page.goto(url + "/node/8/edit")
    page.wait_for_load_state("networkidle")
    page.evaluate("""() => { const e = document.querySelector('.ck-editor__editable').ckeditorInstance;
        e.model.change(w => w.setSelection(w.createPositionAt(e.model.document.getRoot(), 'end'))); e.editing.view.focus(); }""")
    page.click(".ck-toolbar button[data-cke-tooltip-text*='Media']")
    page.wait_for_selector(".media-library-widget-modal .js-media-library-item")
    page.wait_for_timeout(2000)
    page.locator(".media-library-widget-modal .js-media-library-item", has_text="Turnhouse Hill across").locator("input[type='checkbox']").check()
    page.click(".ui-dialog-buttonpane button:has-text('Insert selected')")
    page.wait_for_selector(".ui-dialog", state="detached")
    page.wait_for_timeout(2500)
    scroll_to(page, ".ck-editor", 150)
    snap("09-editor-media")


def gallery_steps(page: Page, site: dict, snap) -> None:
    """Chapter 9, part 5: the Gallery content type, and the first album."""
    url = site["url"]
    drush_php(site, """$s = \\Drupal::entityTypeManager()->getStorage('node'); $s->delete($s->loadByProperties(['type' => 'gallery']));
\\Drupal\\node\\Entity\\NodeType::load('gallery')?->delete();
$m = \\Drupal::entityTypeManager()->getStorage('media');
foreach (['Carnethy Hill from Turnhouse Hill', 'The view from Carnethy Hill', 'Glencorse Reservoir from the hillside', 'A burn in the Pentland Hills in winter'] as $n) { $m->delete($m->loadByProperties(['name' => $n])); }
\\Drupal::entityTypeManager()->getStorage('entity_view_display')->load('media.image.album')?->delete();
\\Drupal::entityTypeManager()->getStorage('entity_view_mode')->load('media.album')?->delete();""")
    delete_fields(site, "node", "field_photos", "field_hike")

    page.goto(url + "/admin/structure/types/add")
    page.fill("#edit-name", "Gallery")
    page.wait_for_timeout(1500)
    page.fill("#edit-description", "A photo album from one of the club's hikes or photo evenings.")
    page.click("text=Display settings")
    page.uncheck("#edit-display-submitted")
    page.click("text=Menu settings")
    page.uncheck("input[name='menu_options[main]']")
    page.click("input[value='Save and manage fields'], button:has-text('Save and manage fields')")
    page.wait_for_load_state("networkidle")

    fields = url + "/admin/structure/types/manage/gallery/fields"
    page.goto(fields)
    page.click("text=Re-use an existing field")
    page.wait_for_selector(".ui-dialog")
    page.wait_for_timeout(2000)
    page.locator(".ui-dialog tr", has_text="field_body").locator("input, button").first.click()
    page.wait_for_url("**/node.gallery.field_body")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='label']", "Description")
    page.fill("textarea[name='description']", "What the album is about: where and when, and anything worth knowing.")
    page.click("input[value='Save settings']")
    page.wait_for_url("**/gallery/fields")
    page.wait_for_load_state("networkidle")

    def photos_settings(p: Page) -> None:
        p.select_option(".ui-dialog select[name='field_storage[subform][cardinality]']", "-1")
        p.wait_for_timeout(2000)
        p.check(".ui-dialog input[name='settings[handler_settings][target_bundles][image]']")
        p.wait_for_timeout(2000)
        dialog_fill(p, "description", "Upload several photos at once: select them all in the file window.")
        p.check(".ui-dialog input[name='required']")

    create_field(page, fields, "Media", "Photos", None, photos_settings)

    def hike_settings(p: Page) -> None:
        p.check(".ui-dialog input[name='settings[handler_settings][target_bundles][hike]']")
        p.wait_for_timeout(2000)
        dialog_fill(p, "description", "The hike the photos are from, if they're from one.")

    create_field(page, fields, "Reference", "Hike", "Content", hike_settings)
    page.goto(fields)
    snap("09-gallery-fields")

    # A media view mode for album photos: the whole photo, not cropped, with its credits.
    page.goto(url + "/admin/structure/display-modes/view/add/media")
    page.fill("input[name='label']", "Album")
    page.wait_for_timeout(1500)
    page.check("input[name='bundles_by_entity[image]']")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    page.goto(url + "/admin/structure/media/manage/image/display/album")
    page.wait_for_load_state("networkidle")
    set_label(page, "field_media_image", "hidden")
    prefix = field_settings(page, "field_media_image")
    page.select_option(f"select[name='{prefix}[image_style]']", "max_1300x1300")
    field_settings_update(page, "field_media_image")
    for field in ("field_photographer", "field_license", "field_source"):
        set_label(page, field, "inline")
    save_display(page)

    page.goto(url + "/admin/structure/types/manage/gallery/display/default")
    page.wait_for_load_state("networkidle")
    for field in ("field_hike",):
        set_label(page, field, "inline")
    set_label(page, "field_photos", "hidden")
    prefix = field_settings(page, "field_photos")
    page.select_option(f"select[name='{prefix}[view_mode]']", "album")
    field_settings_update(page, "field_photos")
    set_weights(page, {"field_hike": 0, "field_body": 1, "field_photos": 2})
    save_display(page)

    page.goto(url + "/node/add/gallery")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='title[0][value]']", "Pentlands, 21 November")
    page.evaluate("h => document.querySelector('.ck-editor__editable').ckeditorInstance.setData(h)", "<p>Our first hike with the new website: Turnhouse Hill and Carnethy Hill, in sun, wind and, near the top, a little snow.</p>")
    page.fill("input[name='field_hike[0][target_id]']", "Turnhouse Hill and Carnethy Hill (7)")
    page.click("input[name='field_photos-media-library-open-button']")
    page.wait_for_selector(".ui-dialog input[type='file']")
    page.wait_for_timeout(1500)
    page.set_viewport_size({"width": WIDTH, "height": 1300})
    library_upload(page, ALBUM, lambda: snap("09-gallery-upload", ".ui-dialog"))
    page.set_viewport_size({"width": WIDTH, "height": 1000})
    page.select_option("select[name='moderation_state[0][state]']", "published") if page.locator("select[name='moderation_state[0][state]']").count() else None
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    path = page.url.replace(url, "")
    as_visitor(page, site, path, "09-gallery-page")

# Chapter 10: taxonomy.
AREAS = [
    # (name, parent, description)
    ("Pentland Hills", None, "<p>A range of hills south-west of Edinburgh, most of it a regional park. The club's favourite: a bus from the city centre takes you to the foot of the hills.</p>"),
    ("Turnhouse Hill", "Pentland Hills", ""),
    ("Carnethy Hill", "Pentland Hills", ""),
    ("Glencorse Reservoir", "Pentland Hills", ""),
    ("Edinburgh", None, "<p>Hills, beaches and viewpoints inside the city: walks you can do in an afternoon.</p>"),
    ("Arthur's Seat", "Edinburgh", ""),
    ("Calton Hill", "Edinburgh", ""),
    ("Portobello", None, ""),
    ("East Lothian", None, "<p>The coast and hills east of Edinburgh.</p>"),
    ("North Berwick Law", "East Lothian", ""),
]
PHOTO_THEMES = ["Landscape", "Water", "Winter", "City"]


def reset_taxonomy(site: dict) -> None:
    delete_fields(site, "node", "field_area")
    delete_fields(site, "taxonomy_term", "field_photo")
    delete_fields(site, "media", "field_themes")
    drush_php(site, """foreach (['areas', 'photo_themes', 'tags'] as $v) {
  $s = \\Drupal::entityTypeManager()->getStorage('taxonomy_term'); $s->delete($s->loadByProperties(['vid' => $v]));
  \\Drupal\\taxonomy\\Entity\\Vocabulary::load($v)?->delete();
}""")


def add_term(page: Page, url: str, vocabulary: str, name: str, parent: str | None = None, description: str = "", shot=None) -> None:
    page.goto(f"{url}/admin/structure/taxonomy/manage/{vocabulary}/add")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='name[0][value]']", name)
    if description:
        page.evaluate("h => document.querySelector('.ck-editor__editable').ckeditorInstance.setData(h)", description)
    if parent:
        page.click("summary:has-text('Relations')")
        page.wait_for_timeout(500)
        page.select_option("select[name='parent[]']", label=parent)
        page.wait_for_timeout(500)
    if shot:
        shot()
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")


def drag_term(page: Page, row: str, target: str | None = None, indent: int = 0, above: bool = False) -> None:
    """Drags a term by its handle below (or above) another row, then to the right to put it under the row above."""
    handle = page.locator(f"tr:has(a:text-is(\"{row}\")) .tabledrag-handle").first
    handle.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    box = handle.bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    if target:
        other = page.locator(f"tr:has(a:text-is(\"{target}\"))").first.bounding_box()
        y = other["y"] + 5 if above else other["y"] + other["height"] - 5
        page.mouse.move(x, y, steps=25)
    for step in range(1, indent * 9 + 1):
        page.mouse.move(x + step * 4, y)
        page.wait_for_timeout(30)
    page.mouse.up()
    page.wait_for_timeout(800)
    page.evaluate("window.getSelection().removeAllRanges()")


def taxonomy_areas_steps(page: Page, site: dict, snap) -> None:
    """Chapter 10, part 1: the Areas vocabulary, its terms and fields, and Area on Hike and Gallery."""
    url = site["url"]
    reset_taxonomy(site)

    page.goto(url + "/admin/structure/taxonomy/add")
    page.fill("input[name='name']", "Areas")
    page.wait_for_timeout(1500)
    page.fill("input[name='description']", "Regions, and the hills and places in them.")
    snap("10-add-vocabulary")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    for name, parent, description in AREAS:
        shot = (lambda: snap("10-add-term")) if name == "Turnhouse Hill" else None
        add_term(page, url, "areas", name, parent, description, shot)
    page.goto(url + "/admin/structure/taxonomy/manage/areas/overview")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    # Portobello was added without a parent: drag it under Edinburgh (down, then right), and Pentland Hills to the top.
    drag_term(page, "Pentland Hills", "East Lothian", above=True)
    drag_term(page, "Portobello", indent=1)
    snap("10-areas-drag")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    snap("10-areas-overview")


def term_id(site: dict, vocabulary: str, name: str) -> str:
    php = "echo current(\\Drupal::entityTypeManager()->getStorage('taxonomy_term')->loadByProperties(['vid' => '%s', 'name' => \"%s\"]))->id();" % (vocabulary, name)
    return drush_php(site, php)


def taxonomy_fields_steps(page: Page, site: dict, snap) -> None:
    """Chapter 10, part 2: a Photo on Areas, and an Area field on Hike and Gallery."""
    url = site["url"]
    delete_fields(site, "node", "field_area")
    delete_fields(site, "taxonomy_term", "field_photo")
    drush_php(site, "\\Drupal::entityTypeManager()->getStorage('entity_view_display')->load('node.gallery.teaser')?->delete();")

    # A photo for each area: a Media field on the vocabulary.
    def photo_settings(p: Page) -> None:
        p.check(".ui-dialog input[name='settings[handler_settings][target_bundles][image]']")
        p.wait_for_timeout(2000)
        dialog_fill(p, "description", "A photo of the area, shown at the top of its page.")

    fields = url + "/admin/structure/taxonomy/manage/areas/overview/fields"
    create_field(page, fields, "Media", "Photo", None, photo_settings)
    page.goto(fields)
    page.wait_for_load_state("networkidle")
    snap("10-area-fields")

    page.goto(url + "/admin/structure/taxonomy/manage/areas/overview/display/default")
    page.wait_for_load_state("networkidle")
    set_label(page, "field_photo", "hidden")
    prefix = field_settings(page, "field_photo")
    page.select_option(f"select[name='{prefix}[view_mode]']", "banner")
    field_settings_update(page, "field_photo")
    set_weights(page, {"field_photo": -10})
    save_display(page)

    pentlands = term_id(site, "areas", "Pentland Hills")
    page.goto(f"{url}/taxonomy/term/{pentlands}/edit")
    page.wait_for_load_state("networkidle")
    page.click("input[name='field_photo-media-library-open-button']")
    page.wait_for_selector(".media-library-widget-modal .js-media-library-item")
    page.wait_for_timeout(2000)
    page.locator(".media-library-widget-modal .js-media-library-item", has_text="The view from Carnethy Hill").locator("input[type='checkbox']").check()
    page.click(".ui-dialog-buttonpane button:has-text('Insert selected')")
    page.wait_for_selector(".ui-dialog", state="detached")
    page.wait_for_timeout(2000)
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    as_visitor(page, site, f"/taxonomy/term/{pentlands}", "10-term-pentland-hills")

    # An Area field on Hike.
    def area_settings(p: Page) -> None:
        p.check(".ui-dialog input[name='settings[handler_settings][target_bundles][areas]']")
        p.wait_for_timeout(2000)
        dialog_fill(p, "description", "Where the hike is. Choose the hill or place; choose the region only if no place fits.")
        dialog_scroll_to(p, "[name='settings[handler_settings][target_bundles][areas]']")

    create_field(page, url + "/admin/structure/types/manage/hike/fields", "Reference", "Area", "Taxonomy term", area_settings,
                 lambda step: snap("10-area-field-settings", ".ui-dialog") if step == "settings" else None)

    page.goto(url + "/admin/structure/types/manage/hike/form-display")
    page.wait_for_load_state("networkidle")
    page.select_option("select[name='fields[field_area][type]']", "options_select")
    page.wait_for_timeout(1500)
    set_weights(page, {"field_date": 1, "field_meeting_place": 2, "field_area": 3, "field_distance": 4, "field_difficulty": 5, "field_hike_leader": 6, "field_body": 7})
    save_display(page)

    page.goto(url + "/admin/structure/types/manage/hike/display/default")
    page.wait_for_load_state("networkidle")
    set_label(page, "field_area", "inline")
    set_weights(page, {"field_date": 2, "field_meeting_place": 3, "field_area": 4, "field_distance": 5, "field_difficulty": 6, "field_hike_leader": 7, "field_body": 8})
    save_display(page)

    page.goto(url + "/node/7/edit")
    page.wait_for_load_state("networkidle")
    page.select_option("select[name='field_area']", label="-Turnhouse Hill")
    page.select_option("select[name='moderation_state[0][state]']", "published")
    page.locator("select[name='field_area']").evaluate("e => e.size = 13")
    scroll_to(page, "select[name='field_area']", 250)
    snap("10-hike-form-area")
    page.locator("select[name='field_area']").evaluate("e => e.size = 0")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    as_visitor(page, site, "/hikes/turnhouse-hill", "10-hike-area")

    # The Try it: Area on Gallery too, and a Teaser for galleries, so the term page lists the album briefly.
    gallery_fields = url + "/admin/structure/types/manage/gallery/fields"
    page.goto(gallery_fields)
    page.click("text=Re-use an existing field")
    page.wait_for_selector(".ui-dialog")
    page.wait_for_timeout(2000)
    page.locator(".ui-dialog tr", has_text="field_area").locator("input, button").first.click()
    page.wait_for_url("**/node.gallery.field_area")
    page.wait_for_load_state("networkidle")
    page.fill("textarea[name='description']", "Where the photos were taken.")
    page.click("input[value='Save settings']")
    page.wait_for_url("**/gallery/fields")
    drush_php(site, """$f = \\Drupal::service('entity_display.repository');
$d = $f->getViewDisplay('node', 'gallery', 'default'); $d->setComponent('field_area', ['label' => 'inline', 'type' => 'entity_reference_label', 'weight' => 1])->save();
$f->getFormDisplay('node', 'gallery', 'default')->setComponent('field_area', ['type' => 'options_select', 'weight' => 2])->save();
$t = $d->createCopy('teaser'); $t->removeComponent('field_photos')->removeComponent('field_hike')
  ->setComponent('field_body', ['label' => 'hidden', 'type' => 'text_trimmed', 'settings' => ['trim_length' => 200], 'weight' => 2])->save();
$n = \\Drupal\\node\\Entity\\Node::load(11); $n->set('field_area', \\Drupal::entityTypeManager()->getStorage('taxonomy_term')->loadByProperties(['vid' => 'areas', 'name' => 'Turnhouse Hill'])); $n->save();""")
    turnhouse = term_id(site, "areas", "Turnhouse Hill")
    as_visitor(page, site, f"/taxonomy/term/{turnhouse}", "10-term-turnhouse-hill")


def taxonomy_themes_steps(page: Page, site: dict, snap) -> None:
    """Chapter 10, part 3: Photo themes, a free-tagging vocabulary on the Image media type."""
    url = site["url"]
    delete_fields(site, "media", "field_themes")
    drush_php(site, """$s = \\Drupal::entityTypeManager()->getStorage('taxonomy_term'); $s->delete($s->loadByProperties(['vid' => 'photo_themes']));
\\Drupal\\taxonomy\\Entity\\Vocabulary::load('photo_themes')?->delete();""")

    page.goto(url + "/admin/structure/taxonomy/add")
    page.fill("input[name='name']", "Photo themes")
    page.wait_for_timeout(1500)
    page.fill("input[name='description']", "What a photo shows. Anyone who uploads a photo can add a theme.")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    for name in PHOTO_THEMES:
        add_term(page, url, "photo_themes", name)

    def themes_settings(p: Page) -> None:
        p.select_option(".ui-dialog select[name='field_storage[subform][cardinality]']", "-1")
        p.wait_for_timeout(2000)
        p.check(".ui-dialog input[name='settings[handler_settings][target_bundles][photo_themes]']")
        p.wait_for_timeout(2000)
        p.check(".ui-dialog input[name='settings[handler_settings][auto_create]']")
        p.wait_for_timeout(1500)
        dialog_fill(p, "description", "What the photo shows, such as Landscape or Winter. Separate themes with commas; a new theme is added to the list.")
        dialog_scroll_to(p, "[name='settings[handler_settings][auto_create]']")

    create_field(page, url + "/admin/structure/media/manage/image/fields", "Reference", "Themes", "Taxonomy term", themes_settings,
                 lambda step: snap("10-themes-field-settings", ".ui-dialog") if step == "settings" else None)

    for mode in ("default", "media_library"):
        page.goto(f"{url}/admin/structure/media/manage/image/form-display/{mode}")
        page.wait_for_load_state("networkidle")
        if mode == "media_library":
            row_weights(page, True)
            page.select_option("select[name='fields[field_themes][region]']", "content")
            page.wait_for_timeout(1500)
            row_weights(page, False)
        page.select_option("select[name='fields[field_themes][type]']", "entity_reference_autocomplete_tags")
        page.wait_for_timeout(1500)
        save_display(page)

    media = drush_php(site, "echo current(\\Drupal::entityTypeManager()->getStorage('media')->loadByProperties(['name' => 'Turnhouse Hill across Glencorse Reservoir']))->id();")
    page.goto(f"{url}/media/{media}/edit")
    page.wait_for_load_state("networkidle")
    box = page.locator("input[name='field_themes[target_id]']")
    scroll_to(page, "input[name='field_themes[target_id]']", 300)
    # Choosing a theme from the suggestions writes its ID after it, as here; Hills is new.
    box.fill(f"Landscape ({term_id(site, 'photo_themes', 'Landscape')}), Water ({term_id(site, 'photo_themes', 'Water')}), Hills")
    page.wait_for_timeout(500)
    snap("10-media-themes")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    page.goto(url + "/admin/structure/taxonomy/manage/photo_themes/overview")
    page.wait_for_load_state("networkidle")
    snap("10-photo-themes")


def cms_tags(page: Page, url: str) -> None:
    page.goto(url + "/node/add/page")
    page.wait_for_load_state("networkidle")
    box = page.locator(".field--name-field-tags .tagify__input").first
    box.scroll_into_view_if_needed()
    box.click()
    for tag in ("Hiking", "Photography"):
        page.keyboard.type(tag + ",")
        page.wait_for_timeout(800)
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)
    scroll_to(page, ".field--name-field-tags", 300)


# Chapter 11: modules and recipes.
def drush(site: dict, *args: str) -> str:
    result = subprocess.run(["ddev", "drush", *args], cwd=site["dir"], check=True, capture_output=True, text=True)
    return result.stdout


def composer(site: dict, *args: str) -> None:
    """Runs Composer, then rebuilds Drupal's cache: Composer rewrites the class list Drupal has cached."""
    subprocess.run(["ddev", "composer", *args], cwd=site["dir"], check=True, capture_output=True)
    subprocess.run(["ddev", "drush", "cache:rebuild"], cwd=site["dir"], check=True, capture_output=True)


def extend_install(page: Page, url: str, module: str, filter_text: str, shot=None) -> None:
    """Installs a downloaded module on Extend, after filtering the list."""
    page.goto(url + "/admin/modules")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.fill("input[name='text']", filter_text)
    page.wait_for_timeout(1000)
    page.check(f"input[name='modules[{module}][enable]']")
    page.wait_for_timeout(500)
    if shot:
        shot()
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    if "has been installed" not in page.content() and "have been installed" not in page.content():
        raise RuntimeError(f"{module} wasn't installed")


def modules_steps(page: Page, site: dict, snap) -> None:
    """Chapter 11, part 1: Diff from Composer, and Project Browser on core. Composer itself runs outside (see the chapter)."""
    url = site["url"]
    drush_php(site, """\\Drupal\\field\\Entity\\FieldConfig::loadByName('node', 'gallery', 'comment')?->delete();
if (\\Drupal::moduleHandler()->moduleExists('comment')) { $s = \\Drupal::entityTypeManager()->getStorage('comment'); $s->delete($s->loadMultiple()); }""")
    delete_fields(site, "node", "comment")
    uninstall(site, "diff", "module_filter", "project_browser", "comment")
    drush_php(site, "\\Drupal::state()->delete('project_browser.applied_recipes');")
    composer(site, "remove", "drupal/module_filter")
    # Back to the hike as Chapter 10 left it: the newest revision from before this chapter becomes the current
    # one again, and the revisions this chapter made are deleted, so the Revisions tab shows one new revision.
    drush_php(site, """$s = \\Drupal::entityTypeManager()->getStorage('node'); $ids = array_reverse(array_keys($s->getQuery()->allRevisions()->accessCheck(FALSE)->condition('nid', 7)->sort('vid')->execute()));
$ours = ['Added a head torch to the list.', 'Back to the description before Chapter 11.'];
$keep = NULL; foreach ($ids as $vid) { $r = $s->loadRevision($vid); if (!in_array($r->getRevisionLogMessage(), $ours) && !str_contains($r->get('field_body')->value, 'head torch')) { $keep = $r; break; } }
if ($keep && !$keep->isDefaultRevision()) { $keep->setNewRevision(FALSE); $keep->isDefaultRevision(TRUE); $keep->save(); }
foreach ($ids as $vid) { $r = $s->loadRevision($vid); if ($keep && $vid != $keep->getRevisionId() && ($vid > $keep->getRevisionId() || in_array($r->getRevisionLogMessage(), $ours))) { $s->deleteRevision($vid); } }""")

    extend_install(page, url, "diff", "diff", lambda: snap("11-extend-diff"))

    # A change worth comparing: one more sentence in the hike's description.
    page.goto(url + "/node/7/edit")
    page.wait_for_load_state("networkidle")
    page.evaluate("""() => { const e = document.querySelector('.ck-editor__editable').ckeditorInstance;
      e.setData(e.getData().replace('and your camera.', 'your camera, and a head torch: it gets dark before five in November.')); }""")
    page.fill("textarea[name='revision_log[0][value]']", "Added a head torch to the list.")
    page.select_option("select[name='moderation_state[0][state]']", "published")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    page.goto(url + "/node/7/revisions")
    page.wait_for_load_state("networkidle")
    snap("11-revisions-compare")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    page.get_by_text("gets dark").first.scroll_into_view_if_needed()
    page.evaluate("window.scrollBy(0, 200)")
    page.wait_for_timeout(500)
    snap("11-diff")

    extend_install(page, url, "project_browser", "project browser")
    browse = url + "/admin/modules/browse/drupalorg_jsonapi"
    page.goto(browse)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(4000)
    snap("11-project-browser")

    def find_module_filter() -> None:
        page.goto(browse)
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)
        page.fill("input[type='search']", "module filter")
        page.keyboard.press("Enter")
        page.wait_for_timeout(4000)

    find_module_filter()
    page.locator("button", has_text="for Module Filter").first.click()
    page.wait_for_timeout(2000)
    snap("11-pb-commands", "[role=dialog], .ui-dialog")

    composer(site, "require", "drupal/module_filter")
    extend_install(page, url, "module_filter", "module filter")
    page.goto(url + "/admin/modules")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    snap("11-module-filter")

    page.goto(url + "/admin/modules/browse/recipes")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    page.fill("input[type='search']", "comments")
    page.keyboard.press("Enter")
    page.wait_for_timeout(3000)
    snap("11-pb-recipes")
    drush(site, "recipe", "core/recipes/comment_base")

    # Comments on albums: re-use the comment field the recipe brought.
    gallery_fields = url + "/admin/structure/types/manage/gallery/fields"
    page.goto(gallery_fields)
    page.click("text=Re-use an existing field")
    page.wait_for_selector(".ui-dialog")
    page.wait_for_timeout(2000)
    snap("11-reuse-comment", ".ui-dialog")
    page.locator(".ui-dialog tr", has_text="comment").locator("input, button").first.click()
    page.wait_for_url("**/node.gallery.comment")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='label']", "Comments")
    page.click("input[value='Save settings']")
    page.wait_for_url("**/gallery/fields")
    page.goto(url + "/node/11")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='subject[0][value]']", "Snow on Carnethy")
    page.evaluate("h => document.querySelector('.ck-editor__editable').ckeditorInstance.setData(h)", "<p>The second photo is my favorite: you can see the snow line on Carnethy Hill.</p>")
    page.click("form.comment-form #edit-submit")
    page.wait_for_load_state("networkidle")
    page.locator("#comments, .comments, section:has(h2:has-text('Comments'))").first.scroll_into_view_if_needed()
    page.evaluate("window.scrollBy(0, -100)")
    page.wait_for_timeout(800)
    snap("11-gallery-comments")


def cms_modules_steps(page: Page, site: dict, snap) -> None:
    """Chapter 11, On Drupal CMS: installing from Project Browser, and Devel Generate (Devel is a dev requirement there)."""
    url = site["url"]
    uninstall(site, "module_filter")
    composer(site, "remove", "drupal/module_filter")

    def find() -> object:
        page.goto(url + "/admin/modules/browse/drupalorg_jsonapi")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(4000)
        page.fill("input[type='search']", "module filter")
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)
        return page.locator("li", has_text="Simplifies module search").first

    card = find()
    page.evaluate("window.scrollBy(0, 350)")
    page.wait_for_timeout(500)
    snap("11-cms-pb-install")
    card.locator("button:text-is('Install')").first.click()
    page.wait_for_timeout(5000)
    if page.locator("a:has-text('unlock link')").count():
        # A lock left by an earlier, interrupted run.
        page.click("a:has-text('unlock link')")
        page.wait_for_load_state("networkidle")
        card = find()
        card.locator("button:text-is('Install')").first.click()
    for _ in range(60):
        page.wait_for_timeout(5000)
        if "Installed" in card.inner_text() or page.locator(".ui-dialog:has-text('Error')").count():
            break
    if "Installed" not in card.inner_text():
        raise RuntimeError("Project Browser didn't install Module Filter")
    snap("11-cms-pb-installed")

    newest = drush_php(site, "echo (int) \\Drupal::entityQuery('node')->accessCheck(FALSE)->sort('nid', 'DESC')->range(0, 1)->execute() ? max(\\Drupal::entityQuery('node')->accessCheck(FALSE)->execute()) : 0;")
    page.goto(url + "/admin/config/development/generate/content")
    page.wait_for_load_state("networkidle")
    page.locator("input[name='node_types[page]']").check(force=True)
    page.fill("input[name='num']", "10")
    page.wait_for_timeout(500)
    snap("11-cms-devel-generate")
    # The same as selecting Generate on the form.
    drush(site, "devel-generate:content", "10", "--bundles=page")
    page.goto(url + "/admin/content")
    page.wait_for_load_state("networkidle")
    snap("11-cms-generated")
    drush_php(site, f"$s = \\Drupal::entityTypeManager()->getStorage('node'); $s->delete($s->loadMultiple(\\Drupal::entityQuery('node')->accessCheck(FALSE)->condition('nid', {int(newest or 0)}, '>')->execute()));")


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
    "08-cms-utility-page-display": ("cms", cms_utility_page_display, True, False),
    "09-cms-focal-point": ("cms", cms_focal_point, True, False),
    "10-cms-tags": ("cms", cms_tags, True, False),
}


# Sequences: several screenshots from one run of steps.
# (site, function, window width, the names it takes)
# Chapter 12: Views. The hikes the chapter asks the reader to add (title, date, meeting place, km,
# difficulty, area, photo media ID, description). Dates are fixed, like the Turnhouse hike's (21 November
# 2026): the "upcoming" screenshots show what they should only when taken before that date, so move the
# dates (here and on node 7) if you retake them later.
MORE_HIKES = [
    ("Arthur's Seat at sunrise", "2026-10-24T06:30:00", "Holyrood Palace car park", 5.5, "moderate", "Arthur's Seat", 10, "An early start for the best light of the day: up Arthur's Seat by the Salisbury Crags path, in time for the sun to rise over the Firth of Forth. Bring a head torch for the way up."),
    ("North Berwick Law and the harbour", "2026-12-05T09:30:00", "North Berwick railway station", 7, "easy", "North Berwick Law", None, "A short climb up North Berwick Law, with the whalebone arch at the top and views to the Bass Rock, then down to the harbour for lunch. We take the train from Edinburgh Waverley at 8:55."),
    ("Glencorse Reservoir loop", "2026-12-19T09:30:00", "Flotterstone car park", 9, "easy", "Glencorse Reservoir", 17, "A gentle walk along the reservoir and back over the lower slopes, good for winter light on the water. A good first hike with the club."),
    ("Pentland Hills ridge", "2027-01-02T09:00:00", "Flotterstone car park", 16, "hard", "Pentland Hills", 18, "The whole ridge, from Turnhouse Hill over Carnethy, Scald Law and the Kips, and back through the glen. A long day, with a lot of climbing: bring plenty of food and water."),
]
NO_HIKES = "<p>No hikes are planned right now. New hikes are usually announced a month ahead, so check back soon.</p>"


def add_more_hikes(site: dict) -> None:
    for title, date, place, km, difficulty, area, photo, body in MORE_HIKES:
        php = """$s = \\Drupal::entityTypeManager()->getStorage('node');
if (!$s->loadByProperties(['title' => %s])) {
  $t = \\Drupal::entityTypeManager()->getStorage('taxonomy_term')->loadByProperties(['vid' => 'areas', 'name' => %s]);
  $d = new \\DateTime(%s, new \\DateTimeZone('Europe/London')); $d->setTimezone(new \\DateTimeZone('UTC'));
  $s->create(['type' => 'hike', 'title' => %s, 'uid' => 1, 'field_date' => $d->format('Y-m-d\\\\TH:i:s'), 'field_meeting_place' => %s, 'field_distance' => %s, 'field_difficulty' => %s, 'field_hike_leader' => 1, 'field_area' => $t ? reset($t)->id() : NULL, 'field_photo' => %s, 'field_body' => ['value' => %s, 'format' => 'basic_html'], 'moderation_state' => 'published'])->save();
}""" % (php_str(title), php_str(area), php_str(date), php_str(title), php_str(place), km, php_str(difficulty), photo if photo else "NULL", php_str(f"<p>{body}</p>"))
        drush_php(site, php)
    # A second album, so the Albums page has more than one.
    drush_php(site, """$s = \\Drupal::entityTypeManager()->getStorage('node');
if (!$s->loadByProperties(['title' => 'Edinburgh, 24 October'])) {
  $h = $s->loadByProperties(['title' => "Arthur's Seat at sunrise"]);
  $t = \\Drupal::entityTypeManager()->getStorage('taxonomy_term')->loadByProperties(['vid' => 'areas', 'name' => 'Edinburgh']);
  $s->create(['type' => 'gallery', 'title' => 'Edinburgh, 24 October', 'uid' => 1, 'field_photos' => [10], 'field_hike' => $h ? reset($h)->id() : NULL, 'field_area' => $t ? reset($t)->id() : NULL, 'field_body' => ['value' => '<p>Sunrise from Arthur\\'s Seat, and the Old Town from Calton Hill on the way home.</p>', 'format' => 'basic_html'], 'moderation_state' => 'published'])->save();
}""")


def php_str(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def views_dialog(page: Page, path: str) -> None:
    """Open a Views UI dialog by its link (the part of the URL after /admin/structure/views/nojs/)."""
    link = page.locator(f"a[href='/admin/structure/views/nojs/{path}']").first
    link.evaluate("e => e.scrollIntoView({block: 'center'})")
    page.wait_for_timeout(300)
    # A click by script: the Navigation sidebar can cover links in the left column. Retried, because a
    # click before Drupal's scripts have attached to the link does nothing.
    for attempt in range(3):
        link.evaluate("e => e.click()")
        try:
            page.wait_for_selector(".ui-dialog", timeout=8000)
            break
        except Exception:
            if attempt == 2:
                raise
    page.wait_for_timeout(1800)


def views_apply(page: Page, label: str = "Apply") -> None:
    page.click(f".ui-dialog-buttonpane button:has-text('{label}')")
    page.wait_for_timeout(2500)


def views_add(page: Page, path: str, search: str, name: str, override: bool = False) -> None:
    """Add a handler (filter, sort, area...) through the Add dialog, and open its settings."""
    views_dialog(page, f"add-handler/{path}")
    if override:
        page.select_option(".ui-dialog select[name='override[dropdown]']", index=1)
        page.wait_for_timeout(1500)
    page.fill(".ui-dialog input[name='override[controls_options_search]']", search)
    page.wait_for_timeout(500)
    page.check(f".ui-dialog input[name='name[{name}]']")
    page.wait_for_timeout(300)
    # The first button: "Apply (all displays)", "Apply (this display)" or "Add and configure fields".
    page.locator(".ui-dialog-buttonpane button").first.click()
    page.wait_for_timeout(2500)


def views_save(page: Page) -> None:
    with page.expect_navigation():
        page.locator("#edit-actions input[value='Save']").evaluate("e => e.click()")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)


def layout_add_view_block(page: Page, url: str, block: str, shot=None) -> None:
    page.goto(url + "/node/3/layout")
    page.wait_for_load_state("networkidle")
    page.locator("a:has-text('Add block')").last.click()
    page.wait_for_timeout(3000)
    if shot:
        page.fill("#drupal-off-canvas input[type='search']", "hikes")
        page.wait_for_timeout(800)
        shot()
    page.click(f"#drupal-off-canvas a:text-is('{block}')")
    page.wait_for_timeout(3000)
    page.click("#drupal-off-canvas input.form-submit.button--primary")
    page.wait_for_timeout(3500)
    page.wait_for_load_state("networkidle")


def views_steps(page: Page, site: dict, snap) -> None:
    """Chapter 12: the Hikes view (page and block), the Photos block, the front page, and Albums."""
    url = site["url"]
    drush_php(site, """foreach (['hikes', 'photos', 'albums', 'news'] as $id) { \\Drupal\\views\\Entity\\View::load($id)?->delete(); }
\\Drupal::entityTypeManager()->getStorage('entity_view_display')->load('media.image.small')?->delete();
\\Drupal::entityTypeManager()->getStorage('entity_view_mode')->load('media.small')?->delete();
foreach (\\Drupal::entityTypeManager()->getStorage('menu_link_content')->loadByProperties(['menu_name' => 'main']) as $l) { if (in_array($l->getTitle(), ['Hikes', 'Albums'])) $l->delete(); }
$n = \\Drupal\\node\\Entity\\Node::load(3); if (!$n->get('layout_builder__layout')->isEmpty()) { $n->set('layout_builder__layout', []); $n->setNewRevision(FALSE); $n->save(); }
\\Drupal::configFactory()->getEditable('views.settings')->set('ui.show.sql_query.enabled', FALSE)->save();""")
    add_more_hikes(site)

    page.goto(url + "/admin/structure/views")
    page.wait_for_load_state("networkidle")
    snap("12-views-list")

    # The Hikes view, with the wizard: a page and a block.
    page.goto(url + "/admin/structure/views/add")
    page.wait_for_load_state("networkidle")
    page.fill("#edit-label", "Hikes")
    page.wait_for_timeout(1500)
    page.select_option("select[name='show[type]']", "hike")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    page.check("input[name='page[create]']")
    page.wait_for_timeout(800)
    page.fill("input[name='page[title]']", "Upcoming hikes")
    page.fill("input[name='page[path]']", "hikes")
    page.fill("input[name='page[items_per_page]']", "10")
    page.check("input[name='page[link]']")
    page.wait_for_timeout(800)
    page.select_option("select[name='page[link_properties][parent]']", "main:")
    page.fill("input[name='page[link_properties][title]']", "Hikes")
    page.check("input[name='block[create]']")
    page.wait_for_timeout(800)
    page.fill("input[name='block[title]']", "Next hikes")
    page.select_option("select[name='block[style][row_plugin]']", "teasers")
    page.fill("input[name='block[items_per_page]']", "3")
    page.set_viewport_size({"width": 1280, "height": 2200})
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    snap("12-add-view", element="main form")
    page.set_viewport_size({"width": 1280, "height": 1000})
    page.click("input[value='Save and edit']")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    snap("12-view-edit")

    # Only upcoming hikes, soonest first.
    views_add(page, "hikes/page_1/filter", "field_date", "node__field_date.field_date_value")
    page.select_option(".ui-dialog select[name='options[operator]']", ">=")
    page.wait_for_timeout(500)
    page.check(".ui-dialog input[name='options[value][type]'][value='offset']")
    page.fill(".ui-dialog input[name='options[value][value]']", "now")
    snap("12-filter-date", element=".ui-dialog")
    views_apply(page)
    views_dialog(page, "handler/hikes/page_1/sort/created")
    views_apply(page, "Remove")
    views_add(page, "hikes/page_1/sort", "field_date", "node__field_date.field_date_value")
    views_apply(page)
    views_add(page, "hikes/page_1/empty", "text", "views.area")
    page.fill(".ui-dialog textarea[name='options[content][value]']", NO_HIKES)
    snap("12-no-results", element=".ui-dialog")
    views_apply(page)
    scroll_to(page, ".views-display-columns")
    snap("12-view-filtered")
    views_save(page)
    as_visitor(page, site, "/hikes", "12-hikes-page")

    # The block: the Card view mode, a more link, and a name for the block list.
    page.goto(url + "/admin/structure/views/view/hikes/edit/block_1")
    page.wait_for_load_state("networkidle")
    views_dialog(page, "display/hikes/block_1/row")
    page.select_option(".ui-dialog select[name='override[dropdown]']", index=1)
    page.wait_for_timeout(1500)
    snap("12-block-override", element=".ui-dialog")
    views_apply(page)
    views_dialog(page, "display/hikes/block_1/row_options")
    page.select_option(".ui-dialog select[name='row_options[view_mode]']", "card")
    snap("12-block-card", element=".ui-dialog")
    views_apply(page)
    views_dialog(page, "display/hikes/block_1/block_description")
    page.fill(".ui-dialog input[name='block_description']", "Next hikes")
    views_apply(page)
    views_dialog(page, "display/hikes/block_1/use_more")
    page.select_option(".ui-dialog select[name='override[dropdown]']", index=1)
    page.wait_for_timeout(1500)
    page.check(".ui-dialog input[name='use_more']")
    page.wait_for_timeout(800)
    page.check(".ui-dialog input[name='use_more_always']")
    page.fill(".ui-dialog input[name='use_more_text']", "All upcoming hikes")
    snap("12-more-link", element=".ui-dialog")
    views_apply(page)
    views_dialog(page, "display/hikes/block_1/link_display")
    page.check(".ui-dialog input[name='link_display'][value='page_1']")
    views_apply(page)
    views_save(page)

    # An exposed filter, on the page only.
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_1")
    page.wait_for_load_state("networkidle")
    views_add(page, "hikes/page_1/filter", "field_difficulty", "node__field_difficulty.field_difficulty_value", override=True)
    page.check(".ui-dialog input[name='options[expose_button][checkbox][checkbox]']")
    page.wait_for_timeout(2500)
    page.fill(".ui-dialog input[name='options[expose][label]']", "Difficulty")
    snap("12-exposed-filter", element=".ui-dialog")
    views_apply(page)
    views_save(page)
    as_visitor(page, site, "/hikes?field_difficulty_value=easy", "12-hikes-easy")

    # Newest photos: a Small view mode for images, and a block of them.
    drush_php(site, """$m = \\Drupal\\Core\\Entity\\Entity\\EntityViewMode::create(['id' => 'media.small', 'label' => 'Small', 'targetEntityType' => 'media']); $m->save();
$d = \\Drupal\\Core\\Entity\\Entity\\EntityViewDisplay::create(['targetEntityType' => 'media', 'bundle' => 'image', 'mode' => 'small', 'status' => TRUE]);
$d->setComponent('field_media_image', ['type' => 'image', 'label' => 'hidden', 'settings' => ['image_style' => 'banner_small', 'image_link' => '', 'image_loading' => ['attribute' => 'lazy']], 'weight' => 0]);
$d->setComponent('field_photographer', ['type' => 'string', 'label' => 'inline', 'weight' => 1]);
foreach (array_keys($d->getComponents()) as $name) { if (!in_array($name, ['field_media_image', 'field_photographer'])) $d->removeComponent($name); }
$d->save();""")
    page.goto(url + "/admin/structure/views/add")
    page.wait_for_load_state("networkidle")
    page.fill("#edit-label", "Photos")
    page.wait_for_timeout(1500)
    page.select_option("select[name='show[wizard_key]']", "media")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    page.select_option("select[name='show[type]']", "image")
    page.wait_for_timeout(1500)
    page.select_option("select[name='show[sort]']", "media_field_data-created:DESC")
    page.check("input[name='block[create]']")
    page.wait_for_timeout(800)
    page.fill("input[name='block[title]']", "Newest photos")
    page.select_option("select[name='block[style][style_plugin]']", "grid_responsive")
    page.wait_for_timeout(800)
    page.select_option("select[name='block[style][row_plugin]']", "entity:media")
    page.wait_for_timeout(800)
    page.fill("input[name='block[items_per_page]']", "6")
    page.click("input[value='Save and edit']")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    views_dialog(page, "display/photos/block_1/row_options")
    page.select_option(".ui-dialog select[name='row_options[view_mode]']", "small")
    views_apply(page)
    views_dialog(page, "display/photos/block_1/style_options")
    page.fill(".ui-dialog input[name='style_options[columns]']", "3")
    snap("12-grid-settings", element=".ui-dialog")
    views_apply(page)
    views_dialog(page, "display/photos/block_1/block_description")
    page.fill(".ui-dialog input[name='block_description']", "Newest photos")
    views_apply(page)
    views_save(page)

    # Both blocks on the Welcome page, with Layout Builder.
    layout_add_view_block(page, url, "Next hikes", shot=lambda: snap("12-lb-choose-block"))
    layout_add_view_block(page, url, "Newest photos")
    page.fill("textarea[name='revision_log[0][value]']", "The next hikes and the newest photos.")
    page.click("input[value='Save layout']")
    page.wait_for_load_state("networkidle")
    as_visitor(page, site, "/", "12-front-page")

    # Albums: a page of Gallery teasers in a grid.
    page.goto(url + "/admin/structure/views/add")
    page.wait_for_load_state("networkidle")
    page.fill("#edit-label", "Albums")
    page.wait_for_timeout(1500)
    page.select_option("select[name='show[type]']", "gallery")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    page.select_option("select[name='show[sort]']", "node_field_data-created:DESC")
    page.check("input[name='page[create]']")
    page.wait_for_timeout(800)
    page.fill("input[name='page[title]']", "Albums")
    page.fill("input[name='page[path]']", "galleries")
    page.select_option("select[name='page[style][style_plugin]']", "grid_responsive")
    page.wait_for_timeout(800)
    page.fill("input[name='page[items_per_page]']", "12")
    page.check("input[name='page[link]']")
    page.wait_for_timeout(800)
    page.select_option("select[name='page[link_properties][parent]']", "main:")
    page.fill("input[name='page[link_properties][title]']", "Albums")
    page.click("input[value='Save and edit']")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    views_dialog(page, "display/albums/page_1/style_options")
    page.fill(".ui-dialog input[name='style_options[columns]']", "2")
    views_apply(page)
    views_save(page)
    as_visitor(page, site, "/galleries", "12-galleries")



# Chapter 13: Going deeper with Views.

def views_new(page: Page, url: str, label: str, steps: list) -> None:
    """The Add view wizard: steps are (name, value) pairs, in order; True checks a checkbox."""
    page.goto(url + "/admin/structure/views/add")
    page.wait_for_load_state("networkidle")
    page.fill("#edit-label", label)
    page.wait_for_timeout(1500)
    for name, value in steps:
        field = page.locator(f"[name='{name}']")
        if value is True:
            field.check()
        elif field.evaluate("e => e.tagName") == "SELECT":
            field.select_option(value)
            page.wait_for_load_state("networkidle")
        else:
            field.fill(value)
        page.wait_for_timeout(1200)
    page.click("input[value='Save and edit']")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)


def views_field_label(page: Page, label: str) -> None:
    create = page.locator(".ui-dialog input[name='options[custom_label]']")
    if create.count() and not create.is_checked():
        create.check()
        page.wait_for_timeout(500)
    page.fill(".ui-dialog input[name='options[label]']", label)


def dialog_open_details(page: Page, summary: str) -> None:
    details = page.locator(f".ui-dialog details:has(summary:has-text('{summary}'))").first
    if details.get_attribute("open") is None:
        details.locator("summary").first.click()
        page.wait_for_timeout(500)


def views_admin_shot(page: Page, url: str, path: str, name: str, full: bool = True) -> None:
    page.goto(url + path)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(500)
    save(page, name, full_page=full)


def views2_reset(site: dict) -> None:
    drush_php(site, """foreach (['photo_credits', 'photographers', 'hike_admin'] as $id) { \\Drupal\\views\\Entity\\View::load($id)?->delete(); }
foreach (\\Drupal::entityTypeManager()->getStorage('block')->loadByProperties(['plugin' => 'views_block:albums-block_1']) as $b) { $b->delete(); }""")
    # Core's term view, as the Taxonomy module ships it.
    drush_php(site, """$f = \\Drupal::service('extension.list.module')->getPath('taxonomy') . '/config/optional/views.view.taxonomy_term.yml';
$data = \\Symfony\\Component\\Yaml\\Yaml::parseFile(DRUPAL_ROOT . '/' . $f);
$v = \\Drupal\\views\\Entity\\View::load('taxonomy_term'); foreach ($data as $k => $val) { if (!in_array($k, ['uuid', '_core'])) $v->set($k, $val); } $v->save();""")


def views2_fields_steps(page: Page, site: dict, snap) -> None:
    """Chapter 13, part 1: a table of photo credits (fields, a reverse relationship) and photographers (aggregation)."""
    url = site["url"]
    views2_reset(site)
    views_new(page, url, "Photo credits", [
        ("show[wizard_key]", "media"), ("show[type]", "image"), ("show[sort]", "media_field_data-name:DESC"),
        ("page[create]", True), ("page[title]", "Photo credits"), ("page[path]", "admin/content/photo-credits"),
        ("page[style][style_plugin]", "table"), ("page[items_per_page]", "50"),
    ])
    # The thumbnail, the photographer, the license and the source.
    views_add(page, "photo_credits/page_1/field", "thumbnail", "media_field_data.thumbnail__target_id")
    views_field_label(page, "Photo")
    page.select_option(".ui-dialog select[name='options[settings][image_style]']", "thumbnail")
    snap("13-field-thumbnail", element=".ui-dialog")
    views_apply(page)
    for search, name in [("photographer", "field_photographer"), ("license", "field_license"), ("source", "field_source")]:
        views_add(page, "photo_credits/page_1/field", search, f"media__{name}.{name}")
        views_apply(page)
    views_dialog(page, "display/photo_credits/page_1/style_options")
    for column in ["name", "field_photographer", "field_license"]:
        page.check(f".ui-dialog input[name='style_options[info][{column}][sortable]']")
    page.check(".ui-dialog input[name='style_options[default]'][value='name']")
    snap("13-table-settings", element=".ui-dialog")
    views_apply(page)
    # Which album is each photo in? The reverse of the albums' Photos field.
    views_add(page, "photo_credits/page_1/relationship", "field_photos", "media_field_data.reverse__node__field_photos")
    snap("13-reverse-relationship", element=".ui-dialog")
    views_apply(page)
    views_add(page, "photo_credits/page_1/field", "title", "node_field_data.title")
    views_field_label(page, "Album")
    views_apply(page)
    views_access(page, "photo_credits/page_1", "access media overview")
    views_save(page)
    views_admin_shot(page, url, "/admin/content/photo-credits", "13-photo-credits")

    # Photographers, counted: aggregation.
    views_new(page, url, "Photographers", [
        ("show[wizard_key]", "media"), ("show[type]", "image"), ("show[sort]", "none"),
        ("page[create]", True), ("page[title]", "Photographers"), ("page[path]", "admin/content/photo-credits/photographers"),
        ("page[style][style_plugin]", "table"), ("page[items_per_page]", "50"),
    ])
    views_dialog(page, "display/photographers/page_1/group_by")
    page.check(".ui-dialog input[name='group_by']")
    snap("13-use-aggregation", element=".ui-dialog")
    views_apply(page)
    views_dialog(page, "handler/photographers/page_1/field/name")
    views_apply(page, "Remove")
    views_add(page, "photographers/page_1/field", "photographer", "media__field_photographer.field_photographer")
    views_apply(page)
    views_add(page, "photographers/page_1/field", "ID", "media_field_data.mid")
    # Adding a field with aggregation on asks for its aggregation type first.
    page.select_option(".ui-dialog select[name='options[group_type]']", "count")
    snap("13-aggregation-count", element=".ui-dialog")
    views_apply(page)
    views_field_label(page, "Photos")
    views_apply(page)
    views_dialog(page, "display/photographers/page_1/style_options")
    page.check(".ui-dialog input[name='style_options[info][field_photographer][sortable]']")
    page.check(".ui-dialog input[name='style_options[default]'][value='field_photographer']")
    views_apply(page)
    views_access(page, "photographers/page_1", "access media overview")
    views_save(page)
    views_admin_shot(page, url, "/admin/content/photo-credits/photographers", "13-photographers", full=False)


def views_access(page: Page, display_path: str, permission: str) -> None:
    """Page settings > Access > Permission: choose which permission the page needs."""
    views_dialog(page, f"display/{display_path}/access_options")
    page.select_option(".ui-dialog select[name='access_options[perm]']", permission)
    views_apply(page)


def views_field_relationship(page: Page, relationship: str) -> None:
    page.select_option(".ui-dialog select[name='options[relationship]']", relationship)
    page.wait_for_timeout(1500)


def views_add_display(page: Page, kind: str) -> None:
    """Add a display (Page, Block, Attachment, Feed) with the Add button above the displays."""
    page.locator(f"#views-display-menu-tabs input[value='{kind}'], input[name='op'][value='{kind}']").first.evaluate("e => e.click()")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)


def views_override_title(page: Page, display_path: str, title: str) -> None:
    views_dialog(page, f"display/{display_path}/title")
    page.select_option(".ui-dialog select[name='override[dropdown]']", index=1)
    page.wait_for_timeout(1500)
    page.fill(".ui-dialog input[name='title']", title)
    views_apply(page)


def views2_hike_admin_steps(page: Page, site: dict, snap) -> None:
    """Chapter 13, part 2: a table of hikes for hike leaders (a relationship to the leader, rewritten results)."""
    url = site["url"]
    drush_php(site, "\\Drupal\\views\\Entity\\View::load('hike_admin')?->delete();")
    views_new(page, url, "Hike admin", [
        ("show[type]", "hike"), ("show[sort]", "none"),
        ("page[create]", True), ("page[title]", "Hikes"), ("page[path]", "admin/content/hikes"),
        ("page[style][style_plugin]", "table"), ("page[items_per_page]", "50"),
    ])
    views_add(page, "hike_admin/page_1/field", "date", "node__field_date.field_date")
    page.select_option(".ui-dialog select[name='options[settings][format_type]']", "medium")
    views_apply(page)
    views_add(page, "hike_admin/page_1/field", "difficulty", "node__field_difficulty.field_difficulty")
    page.check(".ui-dialog input[name='options[exclude]']")
    views_apply(page)
    views_add(page, "hike_admin/page_1/field", "distance", "node__field_distance.field_distance")
    views_field_label(page, "Distance and difficulty")
    page.fill(".ui-dialog input[name='options[settings][scale]']", "1")
    dialog_open_details(page, "Rewrite results")
    page.check(".ui-dialog input[name='options[alter][alter_text]']")
    page.wait_for_timeout(500)
    page.fill(".ui-dialog textarea[name='options[alter][text]']", "{{ field_distance }}, {{ field_difficulty }}")
    dialog_scroll_to(page, "textarea[name='options[alter][text]']")
    snap("13-rewrite", element=".ui-dialog")
    views_apply(page)
    # The hike leader is a user: a relationship, then the user's name.
    views_add(page, "hike_admin/page_1/relationship", "hike leader", "node__field_hike_leader.field_hike_leader")
    views_apply(page)
    views_add(page, "hike_admin/page_1/field", "name", "users_field_data.name")
    views_field_label(page, "Leader")
    snap("13-leader-field", element=".ui-dialog")
    views_apply(page)
    views_dialog(page, "display/hike_admin/page_1/style_options")
    page.check(".ui-dialog input[name='style_options[info][field_date][sortable]']")
    page.check(".ui-dialog input[name='style_options[default]'][value='field_date']")
    page.select_option(".ui-dialog select[name='style_options[info][field_date][default_sort_order]']", "desc")
    views_apply(page)
    views_access(page, "hike_admin/page_1", "access content overview")
    views_save(page)
    views_admin_shot(page, url, "/admin/content/hikes", "13-hike-admin", full=False)


def views2_albums_steps(page: Page, site: dict, snap) -> None:
    """Chapter 13, part 3: albums as fields (the first photo), sorted by their hike's date (a relationship)."""
    url = site["url"]
    views2_restore(site, "albums")
    page.goto(url + "/admin/structure/views/view/albums/edit/page_1")
    page.wait_for_load_state("networkidle")
    views_dialog(page, "display/albums/page_1/row")
    page.check(".ui-dialog input[name='row[type]'][value='fields']")
    views_apply(page)
    if page.locator(".ui-dialog").count():
        views_apply(page)
    views_add(page, "albums/page_1/field", "photos", "node__field_photos.field_photos")
    page.uncheck(".ui-dialog input[name='options[custom_label]']")
    page.select_option(".ui-dialog select[name='options[type]']", "entity_reference_entity_view")
    page.wait_for_timeout(2000)
    page.select_option(".ui-dialog select[name='options[settings][view_mode]']", "small")
    dialog_open_details(page, "Multiple field settings")
    page.fill(".ui-dialog input[name='options[delta_limit]']", "1")
    dialog_scroll_to(page, "input[name='options[delta_limit]']")
    snap("13-first-photo", element=".ui-dialog")
    views_apply(page)
    # The album's hike: its title and its date.
    views_add(page, "albums/page_1/relationship", "field_hike", "node__field_hike.field_hike")
    page.check(".ui-dialog input[name='options[required]']")
    snap("13-hike-relationship", element=".ui-dialog")
    views_apply(page)
    views_add(page, "albums/page_1/field", "title", "node_field_data.title")
    views_field_relationship(page, "field_hike")
    views_field_label(page, "Hike")
    page.check(".ui-dialog input[name='options[element_label_colon]']")
    views_apply(page)
    views_add(page, "albums/page_1/field", "date", "node__field_date.field_date")
    views_field_relationship(page, "field_hike")
    page.uncheck(".ui-dialog input[name='options[custom_label]']")
    views_apply(page)
    views_dialog(page, "handler/albums/page_1/sort/created")
    views_apply(page, "Remove")
    views_add(page, "albums/page_1/sort", "field_date", "node__field_date.field_date_value")
    views_field_relationship(page, "field_hike")
    page.check(".ui-dialog input[name='options[order]'][value='DESC']")
    views_apply(page)
    views_save(page)
    as_visitor(page, site, "/galleries", "13-galleries")

    # One row per photo: what a relationship to a multiple-value field does (not saved).
    views_add(page, "albums/page_1/relationship", "field_photos", "node__field_photos.field_photos")
    views_apply(page)
    views_add(page, "albums/page_1/field", "photographer", "media__field_photographer.field_photographer")
    views_apply(page)
    page.wait_for_timeout(2000)
    scroll_to(page, ".view-content")
    page.mouse.move(1200, 600)
    page.wait_for_timeout(800)
    snap("13-duplicates")
    # Throw the experiment away (what Cancel does).
    drush_php(site, "\\Drupal::service('tempstore.shared')->get('views')->delete('albums');")
    page.wait_for_load_state("networkidle")


def views_argument_title(page: Page, title: str) -> None:
    """A contextual filter's Override title, under When the filter value IS in the URL."""
    dialog_open_details(page, "When the filter value IS in the URL")
    page.check(".ui-dialog input[name='options[title_enable]']")
    page.wait_for_timeout(500)
    page.fill(".ui-dialog input[name='options[title]']", title)


def views2_restore(site: dict, *views: str) -> None:
    """Put views back as Chapter 12 leaves them (tools/fixtures/chapter-12/), and drop unsaved changes."""
    for view in views:
        restore_config(site, f"views.view.{view}", "chapter-12")
    drush_php(site, "$t = \\Drupal::service('tempstore.shared')->get('views'); foreach (%s as $v) { $t->delete($v); } drupal_flush_all_caches();" % ("['" + "', '".join(views + ("taxonomy_term",)) + "']"))


def views2_contextual_steps(page: Page, site: dict, snap) -> None:
    """Chapter 13, part 4: contextual filters (term pages with depth, albums from this hike, a member's hikes, an archive)."""
    url = site["url"]
    views2_restore(site, "hikes")
    drush_php(site, """foreach (\\Drupal::entityTypeManager()->getStorage('block')->loadByProperties(['plugin' => 'views_block:albums-block_1']) as $b) { $b->delete(); }
$v = \\Drupal\\views\\Entity\\View::load('albums'); $d = $v->get('display'); unset($d['block_1']); $v->set('display', $d); $v->save();
$f = \\Drupal::service('extension.list.module')->getPath('taxonomy') . '/config/optional/views.view.taxonomy_term.yml';
$data = \\Symfony\\Component\\Yaml\\Yaml::parseFile(DRUPAL_ROOT . '/' . $f);
$v = \\Drupal\\views\\Entity\\View::load('taxonomy_term'); foreach ($data as $k => $val) { if (!in_array($k, ['uuid', '_core'])) $v->set($k, $val); } $v->save();""")
    pentland = term_id(site, "areas", "Pentland Hills")
    as_visitor(page, site, f"/taxonomy/term/{pentland}", "13-term-before")

    # Term pages with depth: swap the term view's contextual filter.
    page.goto(url + "/admin/structure/views/view/taxonomy_term/edit/page_1")
    page.wait_for_load_state("networkidle")
    scroll_to(page, ".views-display-columns")
    snap("13-term-view")
    views_dialog(page, "handler/taxonomy_term/page_1/argument/tid")
    views_apply(page, "Remove")
    views_add(page, "taxonomy_term/page_1/argument", "depth", "node_field_data.term_node_tid_depth")
    page.select_option(".ui-dialog select[name='options[depth]']", "2")
    page.check(".ui-dialog input[name='options[default_action]'][value='not found']")
    views_argument_title(page, "{{ arguments.term_node_tid_depth }}")
    page.check(".ui-dialog input[name='options[specify_validation]']")
    page.wait_for_timeout(800)
    page.select_option(".ui-dialog select[name='options[validate][type]']", "entity---taxonomy_term")
    page.wait_for_timeout(1500)
    dialog_scroll_to(page, "select[name='options[depth]']")
    snap("13-depth", element=".ui-dialog")
    views_apply(page)
    # The header shows the term itself; it still points at the old contextual filter.
    views_dialog(page, "handler/taxonomy_term/page_1/header/entity_taxonomy_term")
    page.fill(".ui-dialog input[name='options[target]']", "{{ raw_arguments.term_node_tid_depth }}")
    snap("13-header-target", element=".ui-dialog")
    views_apply(page)
    views_save(page)
    as_visitor(page, site, f"/taxonomy/term/{pentland}", "13-term-after")

    # Albums from this hike: a block whose contextual filter takes the hike from the page it's on.
    page.goto(url + "/admin/structure/views/view/albums/edit/page_1")
    page.wait_for_load_state("networkidle")
    views_add_display(page, "Block")
    views_override_title(page, "albums/block_1", "Albums from this hike")
    views_add(page, "albums/block_1/argument", "hike", "node__field_hike.field_hike_target_id", override=True)
    page.check(".ui-dialog input[name='options[default_action]'][value='default']")
    page.wait_for_timeout(800)
    page.select_option(".ui-dialog select[name='options[default_argument_type]']", "node")
    page.wait_for_timeout(800)
    snap("13-default-argument", element=".ui-dialog")
    views_apply(page)
    views_dialog(page, "display/albums/block_1/block_description")
    page.fill(".ui-dialog input[name='block_description']", "Albums from this hike")
    views_apply(page)
    views_dialog(page, "display/albums/block_1/block_hide_empty")
    page.check(".ui-dialog input[name='block_hide_empty']")
    views_apply(page)
    views_save(page)
    drush_php(site, """\\Drupal\\block\\Entity\\Block::create(['id' => 'olivero_albums_from_this_hike', 'theme' => 'olivero', 'region' => 'content', 'weight' => 100, 'plugin' => 'views_block:albums-block_1', 'settings' => ['id' => 'views_block:albums-block_1', 'label' => '', 'label_display' => 'visible', 'provider' => 'views', 'items_per_page' => 'none'], 'visibility' => ['entity_bundle:node' => ['id' => 'entity_bundle:node', 'negate' => FALSE, 'context_mapping' => ['node' => '@node.node_route_context:node'], 'bundles' => ['hike' => 'hike']]]])->save();""")
    as_visitor(page, site, "/hikes/turnhouse-hill", "13-hike-albums")

    # The hikes a member leads: a tab on their profile.
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_1")
    page.wait_for_load_state("networkidle")
    views_add_display(page, "Page")
    views_dialog(page, "display/hikes/page_2/path")
    page.fill(".ui-dialog input[name='path']", "user/%user/hikes")
    views_apply(page)
    views_dialog(page, "display/hikes/page_2/menu")
    page.check(".ui-dialog input[name='menu[type]'][value='tab']")
    page.wait_for_timeout(800)
    page.fill(".ui-dialog input[name='menu[title]']", "Hikes")
    snap("13-menu-tab", element=".ui-dialog")
    views_apply(page)
    views_add(page, "hikes/page_2/argument", "hike leader", "node__field_hike_leader.field_hike_leader_target_id", override=True)
    views_argument_title(page, "Hikes led by {{ arguments.field_hike_leader_target_id }}")
    views_apply(page)
    views_save(page)
    views_admin_shot(page, url, "/user/1/hikes", "13-user-hikes", full=False)

    # An archive by month: a summary when there's no month in the address.
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_1")
    page.wait_for_load_state("networkidle")
    views_add_display(page, "Page")
    views_dialog(page, "display/hikes/page_3/path")
    page.fill(".ui-dialog input[name='path']", "hikes/archive")
    views_apply(page)
    views_override_title(page, "hikes/page_3", "Hike archive")
    views_dialog(page, "handler/hikes/page_3/filter/field_date_value")
    page.select_option(".ui-dialog select[name='override[dropdown]']", index=1)
    page.wait_for_timeout(1500)
    views_apply(page, "Remove")
    views_add(page, "hikes/page_3/argument", "date", "node__field_date.field_date_value_year_month", override=True)
    page.check(".ui-dialog input[name='options[default_action]'][value='summary']")
    page.wait_for_timeout(800)
    page.check(".ui-dialog input[name='options[summary][sort_order]'][value='desc']")
    page.check(".ui-dialog input[name='options[summary][format]'][value='default_summary']")
    page.wait_for_timeout(800)
    views_argument_title(page, "Hikes in {{ arguments.field_date_value_year_month }}")
    dialog_scroll_to(page, "input[name='options[default_action]'][value='summary']")
    snap("13-summary", element=".ui-dialog")
    views_apply(page)
    views_save(page)
    as_visitor(page, site, "/hikes/archive", "13-archive")


def views2_more_steps(page: Page, site: dict, snap) -> None:
    """Chapter 13, part 5: an attachment, a feed, caching and the SQL (run after views2_contextual_steps)."""
    url = site["url"]
    drush_php(site, "$v = \\Drupal\\views\\Entity\\View::load('hikes'); $d = $v->get('display'); unset($d['attachment_1'], $d['feed_1']); $v->set('display', $d); $v->save(); \\Drupal::service('tempstore.shared')->get('views')->delete('hikes');")

    # An attachment: the list of months above every month of the archive.
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_3")
    page.wait_for_load_state("networkidle")
    views_add_display(page, "Attachment")
    views_dialog(page, "display/hikes/attachment_1/displays")
    page.check(".ui-dialog input[name='displays[page_3]']")
    views_apply(page)
    views_dialog(page, "display/hikes/attachment_1/inherit_arguments")
    page.uncheck(".ui-dialog input[name='inherit_arguments']")
    views_apply(page)
    views_dialog(page, "handler/hikes/attachment_1/filter/field_date_value")
    page.select_option(".ui-dialog select[name='override[dropdown]']", index=1)
    page.wait_for_timeout(1500)
    views_apply(page, "Remove")
    views_add(page, "hikes/attachment_1/argument", "date", "node__field_date.field_date_value_year_month", override=True)
    page.check(".ui-dialog input[name='options[default_action]'][value='summary']")
    page.wait_for_timeout(800)
    page.check(".ui-dialog input[name='options[summary][sort_order]'][value='desc']")
    page.check(".ui-dialog input[name='options[summary][format]'][value='default_summary']")
    page.wait_for_timeout(800)
    views_apply(page)
    # Now the attachment lists the months, so the page itself shows all hikes when there's no month.
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_3")
    page.wait_for_load_state("networkidle")
    views_dialog(page, "handler/hikes/page_3/argument/field_date_value_year_month")
    page.check(".ui-dialog input[name='options[default_action]'][value='ignore']")
    page.wait_for_timeout(800)
    views_apply(page)
    views_save(page)
    page.goto(url + "/admin/structure/views/view/hikes/edit/attachment_1")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    snap("13-attachment")
    as_visitor(page, site, "/hikes/archive/202612", "13-archive-attachment")

    # A feed of upcoming hikes, with its icon on the hikes page.
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_1")
    page.wait_for_load_state("networkidle")
    views_add_display(page, "Feed")
    views_dialog(page, "display/hikes/feed_1/path")
    page.fill(".ui-dialog input[name='path']", "hikes/feed")
    views_apply(page)
    views_dialog(page, "display/hikes/feed_1/displays")
    page.check(".ui-dialog input[name='displays[page_1]']")
    views_apply(page)
    views_save(page)
    page.goto(url + "/admin/structure/views/view/hikes/edit/feed_1")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    snap("13-feed")
    as_visitor(page, site, "/hikes", "13-feed-icon")

    # Caching.
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_1")
    page.wait_for_load_state("networkidle")
    views_dialog(page, "display/hikes/page_1/cache")
    snap("13-caching", element=".ui-dialog")
    page.locator(".ui-dialog-buttonpane button", has_text="Cancel").first.click()
    page.wait_for_timeout(1000)

    # Under the hood: the SQL in the preview of the albums view, with its joins.
    drush_php(site, "\\Drupal::configFactory()->getEditable('views.settings')->set('ui.show.sql_query.enabled', TRUE)->save();")
    try:
        page.goto(url + "/admin/structure/views/view/albums/edit/page_1")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        page.locator(".views-query-info").scroll_into_view_if_needed()
        snap("13-sql", element=".views-query-info")
    finally:
        drush_php(site, "\\Drupal::configFactory()->getEditable('views.settings')->set('ui.show.sql_query.enabled', FALSE)->save();")


def views2_displays_steps(page: Page, site: dict, snap) -> None:
    """Chapter 13, Displays in depth: the Add menu, the display's actions, and the Views settings (after views2_more_steps)."""
    url = site["url"]
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_1")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.locator("#views-display-menu-tabs li.add > a").first.evaluate("e => e.click()")
    page.wait_for_timeout(800)
    page.mouse.move(1200, 900)
    snap("13-add-display")
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_2")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.locator(".views-display-columns, #edit-display-settings-top").first.scroll_into_view_if_needed()
    page.locator("#edit-display-settings-top .dropbutton-toggle button, .views-ui-display-tab-actions .dropbutton-toggle button").first.evaluate("e => e.click()")
    page.wait_for_timeout(800)
    snap("13-display-actions")
    page.goto(url + "/admin/structure/views/settings")
    page.wait_for_load_state("networkidle")
    snap("13-views-settings")


def views2_answer_steps(page: Page, site: dict, snap) -> None:
    """Appendix C, the answer to Exercise 13.6: the next hike in an attachment, the rest with an offset (after views2_more_steps; undone at the end)."""
    url = site["url"]
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_1")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    # A new attachment. (Not Duplicate as Attachment: the copy would share the page's pager, and
    # its Items to display would change every display that shares it.)
    views_add_display(page, "Attachment")
    display = page.url.rstrip("/").split("/")[-1]
    views_dialog(page, f"display/hikes/{display}/display_title")
    page.fill(".ui-dialog input[name='display_title']", "Next hike")
    views_apply(page)
    # The same exposed filter as the page, so that the attachment has something to inherit.
    views_add(page, f"hikes/{display}/filter", "field_difficulty", "node__field_difficulty.field_difficulty_value", override=True)
    page.check(".ui-dialog input[name='options[expose_button][checkbox][checkbox]']")
    page.wait_for_timeout(1500)
    page.fill(".ui-dialog input[name='options[expose][label]']", "Difficulty")
    views_apply(page)
    views_dialog(page, f"display/hikes/{display}/displays")
    page.check(".ui-dialog input[name='displays[page_1]']")
    views_apply(page)
    views_dialog(page, f"display/hikes/{display}/inherit_exposed_filters")
    page.check(".ui-dialog input[name='inherit_exposed_filters']")
    views_apply(page)
    # A new attachment's pager is its own.
    views_dialog(page, f"display/hikes/{display}/pager_options")
    page.fill(".ui-dialog input[name='pager_options[items_per_page]']", "1")
    views_apply(page)
    page.wait_for_timeout(1000)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(500)
    snap("appendix-c-next-hike-attachment")
    # The page skips the hike the attachment shows.
    page.goto(url + "/admin/structure/views/view/hikes/edit/page_1")
    page.wait_for_load_state("networkidle")
    views_dialog(page, "display/hikes/page_1/pager")
    if page.locator(".ui-dialog select[name='override[dropdown]']").count():
        page.select_option(".ui-dialog select[name='override[dropdown]']", index=1)
        page.wait_for_timeout(1500)
    page.check(".ui-dialog input[name='pager[type]'][value='mini']")
    views_apply(page)
    if not page.locator(".ui-dialog input[name='pager_options[offset]']").count():
        views_dialog(page, "display/hikes/page_1/pager_options")
    page.fill(".ui-dialog input[name='pager_options[offset]']", "1")
    dialog_scroll_to(page, "input[name='pager_options[offset]']")
    snap("appendix-c-offset", element=".ui-dialog")
    views_apply(page)
    views_save(page)
    as_visitor(page, site, "/hikes?field_difficulty_value=easy", "appendix-c-easy")
    # Undo, so the hikes view stays as Chapter 13 leaves it.
    drush_php(site, """$v = \\Drupal\\views\\Entity\\View::load('hikes'); $d = $v->get('display');
foreach ($d as $id => $x) { if ($x['display_plugin'] == 'attachment' && $id != 'attachment_1') unset($d[$id]); }
unset($d['page_1']['display_options']['pager']); $d['page_1']['display_options']['defaults']['pager'] = TRUE;
$d['default']['display_options']['pager']['options']['items_per_page'] = 10;
$v->set('display', $d); $v->save();""")


def views2_album_count_undo(site: dict) -> None:
    """The Albums view as Chapter 13 leaves it: no aggregation, no relationship to the photos, no count."""
    drush_php(site, """\\Drupal::service('tempstore.shared')->get('views')->delete('albums');
$v = \\Drupal\\views\\Entity\\View::load('albums'); $d = $v->get('display');
foreach ($d as $id => $x) {
  $o =& $d[$id]['display_options'];
  unset($o['group_by'], $o['relationships']['field_photos'], $o['fields']['mid']);
  if (isset($o['fields']['field_photos'])) { $o['fields']['field_photos']['group_column'] = 'target_id'; }
  unset($o);
}
$v->set('display', $d); $v->save();""")


def views2_album_count_steps(page: Page, site: dict, snap) -> None:
    """Appendix C, the answer to Exercise 13.7: the number of photos in each album (after views2_albums_steps; undone at the end)."""
    url = site["url"]
    views2_album_count_undo(site)
    page.goto(url + "/admin/structure/views/view/albums/edit/page_1")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    views_dialog(page, "display/albums/page_1/group_by")
    page.check(".ui-dialog input[name='group_by']")
    views_apply(page)
    views_add(page, "albums/page_1/relationship", "field_photos", "node__field_photos.field_photos")
    views_apply(page)
    views_add(page, "albums/page_1/field", "ID", "media_field_data.mid")
    page.select_option(".ui-dialog select[name='options[group_type]']", "count")
    views_apply(page)
    views_field_relationship(page, "field_photos")
    views_field_label(page, "Photos")
    page.check(".ui-dialog input[name='options[element_label_colon]']")
    views_apply(page)
    # The trap: the first photo's field groups by each photo's ID, so every album and photo is a row of its own.
    page.wait_for_timeout(2000)
    scroll_to(page, ".view-content")
    page.mouse.move(1200, 600)
    page.wait_for_timeout(800)
    snap("appendix-c-count-duplicates")
    # Group the first photo's field by the album instead.
    views_dialog(page, "handler-group/albums/page_1/field/field_photos")
    page.select_option(".ui-dialog select[name='options[group_column]']", "entity_id")
    page.wait_for_timeout(500)
    snap("appendix-c-group-column", element=".ui-dialog")
    views_apply(page)
    views_save(page)
    as_visitor(page, site, "/galleries", "appendix-c-album-count")
    views2_album_count_undo(site)


# Chapter 14: blocks, regions and menus.

CH14_BLOCKS = ["olivero_next_hikes", "olivero_newest_photos", "olivero_club_info", "olivero_join_the_club", "olivero_footer"]


def blocks14_reset(site: dict) -> None:
    """The site as Chapter 13 leaves it: no Chapter 14 blocks, block type, menu links or Privacy page; menus in their old order."""
    ids = "', '".join(CH14_BLOCKS)
    drush_php(site, f"""$et = \\Drupal::entityTypeManager();
foreach (['{ids}'] as $id) {{ $et->getStorage('block')->load($id)?->delete(); }}
foreach ($et->getStorage('block_content')->loadByProperties(['reusable' => TRUE]) as $b) {{ $b->delete(); }}
$et->getStorage('block_content_type')->load('club_info')?->delete();
foreach ($et->getStorage('menu_link_content')->loadByProperties(['menu_name' => 'footer']) as $l) {{ $l->delete(); }}
foreach ($et->getStorage('menu_link_content')->loadByProperties(['title' => 'Hike archive']) as $l) {{ $l->delete(); }}
foreach ($et->getStorage('menu_link_content')->loadByProperties(['menu_name' => 'main']) as $l) {{ $l->set('weight', $l->getTitle() == 'About' ? 1 : 2)->set('expanded', FALSE)->save(); }}
foreach ($et->getStorage('node')->loadByProperties(['title' => 'Privacy']) as $n) {{ $n->delete(); }}
foreach (['hikes', 'albums'] as $id) {{ $v = \\Drupal\\views\\Entity\\View::load($id); $d = $v->get('display'); $d['page_1']['display_options']['menu']['weight'] = 0; $d['page_1']['display_options']['menu']['expanded'] = FALSE; $v->set('display', $d); $v->save(); }}
\\Drupal::service('menu_link.static.overrides')->deleteMultipleOverrides(['standard.front_page']);
\\Drupal::service('plugin.manager.menu.link')->rebuild();
drupal_flush_all_caches();""")


def place_block(page: Page, url: str, plugin: str, region: str, block_id: str, label: str | None = None, show_label: bool = True, setup=None, shot=None) -> None:
    """Places a block in Olivero through its Configure block form (what Place block opens)."""
    page.goto(f"{url}/admin/structure/block/add/{plugin}/olivero?region={region}")
    page.wait_for_load_state("networkidle")
    page.evaluate("v => { const e = document.querySelector(\"input[name='id']\"); e.value = v; }", block_id)
    if label is not None:
        page.fill("input[name='settings[label]']", label)
    if not show_label:
        page.uncheck("input[name='settings[label_display]']")
    if setup:
        setup(page)
    if shot:
        shot()
    page.click("input[value='Save block']")
    page.wait_for_load_state("networkidle")


def block_visibility_tab(page: Page, tab: str) -> None:
    page.locator(".vertical-tabs__menu-item a, .vertical-tabs__menu a", has_text=tab).first.click()
    page.wait_for_timeout(600)


def visitor_shot(page: Page, site: dict, path: str, name: str, element: str | None = None, hover: str | None = None, full: bool = False) -> None:
    """A screenshot of path, logged out: the window, the whole page, or one element; optionally hovering over something first."""
    context = page.context.browser.new_context(viewport={"width": WIDTH, "height": 1000}, device_scale_factor=2, ignore_https_errors=True)
    visit = context.new_page()
    visit.goto(site["url"] + path)
    visit.wait_for_load_state("networkidle")
    if hover:
        visit.locator(hover).first.hover()
        visit.wait_for_timeout(1200)
    if element:
        # Olivero's header follows you down the page; keep it out of a shot of one element.
        visit.add_style_tag(content=".site-header__fixable, .is-fixed .site-header__fixable { position: absolute !important; }")
        visit.locator(element).first.scroll_into_view_if_needed()
        visit.wait_for_timeout(500)
    save(visit, name, full_page=full, element=element)
    context.close()


def blocks14_steps(page: Page, site: dict, snap) -> None:
    """Chapter 14, part 1: the block layout, regions, placing blocks and visibility."""
    url = site["url"]
    blocks14_reset(site)

    # The block layout and the regions.
    # The whole Block layout, in a window as tall as the page: a full-page shot would show the fixed admin sidebar over it.
    page.goto(url + "/admin/structure/block")
    page.wait_for_load_state("networkidle")
    row_weights(page, False)
    page.set_viewport_size({"width": WIDTH, "height": page.evaluate("document.documentElement.scrollHeight")})
    page.wait_for_timeout(800)
    save(page, "14-block-layout")
    page.set_viewport_size({"width": WIDTH, "height": 1000})
    page.goto(url + "/admin/structure/block/demo/olivero")
    page.wait_for_load_state("networkidle")
    page.add_style_tag(content=".admin-toolbar, .admin-toolbar-control-bar { display: none !important; } body { padding-inline-start: 0 !important; margin-inline-start: 0 !important; } .dialog-off-canvas-main-canvas { margin-inline-start: 0 !important; }")
    page.wait_for_timeout(800)
    save(page, "14-regions", full_page=True)

    # Place block: the list of blocks, filtered.
    page.goto(url + "/admin/structure/block")
    page.wait_for_load_state("networkidle")
    page.locator("a[href*='/admin/structure/block/library/olivero?region=sidebar']").first.evaluate("e => e.click()")
    page.wait_for_selector(".ui-dialog input[type='search'], .ui-dialog input.block-filter-text")
    page.wait_for_timeout(1500)
    page.locator(".ui-dialog input[type='search'], .ui-dialog input.block-filter-text").first.press_sequentially("hikes", delay=80)
    page.mouse.move(5, 5)
    page.wait_for_timeout(1000)
    snap("14-place-block", element=".ui-dialog")

    # Next hikes in the sidebar, on hike pages only.
    def next_hikes(p: Page) -> None:
        block_visibility_tab(p, "Content type")
        p.check("input[name='visibility[entity_bundle:node][bundles][hike]']")
        p.wait_for_timeout(500)

    def next_hikes_shot() -> None:
        scroll_to(page, "input[name='visibility[entity_bundle:node][bundles][hike]']", 400)
        snap("14-configure-block")

    place_block(page, url, "views_block:hikes-block_1", "sidebar", "olivero_next_hikes", setup=next_hikes, shot=next_hikes_shot)

    # Newest photos in Footer Top, on every page except the front page (which has them already).
    def newest_photos(p: Page) -> None:
        block_visibility_tab(p, "Pages")
        p.fill("textarea[name='visibility[request_path][pages]']", "<front>")
        p.check("input[name='visibility[request_path][negate]'][value='1']")

    def newest_photos_shot() -> None:
        scroll_to(page, "textarea[name='visibility[request_path][pages]']", 300)
        snap("14-visibility-pages")

    place_block(page, url, "views_block:photos-block_1", "footer_top", "olivero_newest_photos", setup=newest_photos, shot=newest_photos_shot)
    visitor_shot(page, site, "/hikes/turnhouse-hill", "14-sidebar", full=True)


def blocks14_content_steps(page: Page, site: dict, snap) -> None:
    """Chapter 14, part 2: content blocks (a Club info block type for the footer, a Join the club block for visitors). After blocks14_steps."""
    url = site["url"]
    views_admin_shot(page, url, "/admin/structure/block-content", "14-block-types", full=False)

    # A block type of our own, with fields.
    page.goto(url + "/admin/structure/block-content/add")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='label']", "Club info")
    page.wait_for_timeout(1500)
    page.fill("textarea[name='description']", "The club's contact details and meeting times, for the footer.")
    page.click("input[value='Save and manage fields']")
    page.wait_for_load_state("networkidle")
    fields = url + "/admin/structure/block-content/manage/club_info/fields"
    create_field(page, fields, "Formatted text", "Meeting times", "Long text")
    create_field(page, fields, "Email", "Email", None)

    def links(p: Page) -> None:
        p.select_option(".ui-dialog select[name='field_storage[subform][cardinality]']", "-1")
        p.wait_for_timeout(2000)
        p.check(".ui-dialog input[name='settings[link_type]'][value='16']")
        p.check(".ui-dialog input[name='settings[title]'][value='2']")

    create_field(page, fields, "Link", "Follow us", None, links)
    page.goto(fields)
    page.wait_for_load_state("networkidle")
    snap("14-club-info-fields")

    # The content block itself.
    page.goto(url + "/block/add/club_info")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='info[0][value]']", "Club info")
    page.evaluate("h => [...document.querySelectorAll('.ck-editor__editable')].pop().ckeditorInstance.setData(h)",
                  "<p><strong>Hikes:</strong> every other Saturday at 9:30.<br><strong>Photo evenings:</strong> the first Thursday of the month at 19:00, in a café in Leith.</p>")
    page.fill("input[name='field_email[0][value]']", "hello@lens-and-trail.ddev.site")
    page.fill("input[name='field_follow_us[0][uri]']", "https://www.flickr.com/groups/lens-and-trail/")
    page.fill("input[name='field_follow_us[0][title]']", "Flickr")
    page.wait_for_timeout(1000)
    snap("14-add-club-info")
    page.click("input[value='Save and configure']")
    page.wait_for_load_state("networkidle")
    # Save and configure goes on to the block's Configure block form, for the default theme.
    page.evaluate("v => { const e = document.querySelector(\"input[name='id']\"); if (e) e.value = v; }", "olivero_club_info")
    page.select_option("select[name='region']", "footer_top")
    page.uncheck("input[name='settings[label_display]']")
    page.click("input[value='Save block']")
    page.wait_for_load_state("networkidle")

    # Club info before Newest photos in Footer Top.
    # (The book drags the row; the script sets the weights.)
    drush_php(site, "\\Drupal\\block\\Entity\\Block::load('olivero_club_info')->setWeight(-10)->save(); \\Drupal\\block\\Entity\\Block::load('olivero_newest_photos')->setWeight(0)->save();")
    page.goto(url + "/admin/structure/block")
    page.wait_for_load_state("networkidle")
    row_weights(page, False)
    page.wait_for_timeout(800)
    scroll_to(page, "tr.region-title-footer_top", 150)
    snap("14-footer-top")

    # Join the club: a Basic block, for visitors only, not on the page about joining.
    page.goto(url + "/block/add/basic")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='info[0][value]']", "Join the club")
    page.evaluate("h => [...document.querySelectorAll('.ck-editor__editable')].pop().ckeditorInstance.setData(h)",
                  "<p>New members are always welcome, whether you bring a camera, boots, or both. Membership is £20 a year, £10 for students.</p><p><a href=\"/join\">How to join</a></p>")
    page.wait_for_timeout(1000)
    page.click("input[value='Save']")
    page.wait_for_load_state("networkidle")
    views_admin_shot(page, url, "/admin/content/block", "14-content-blocks", full=False)
    uuid = drush_php(site, "echo current(\\Drupal::entityTypeManager()->getStorage('block_content')->loadByProperties(['info' => 'Join the club']))->uuid();").strip()

    def join(p: Page) -> None:
        block_visibility_tab(p, "Roles")
        p.check("input[name='visibility[user_role][roles][anonymous]']")
        block_visibility_tab(p, "Pages")
        p.fill("textarea[name='visibility[request_path][pages]']", "/join")
        p.check("input[name='visibility[request_path][negate]'][value='1']")
        block_visibility_tab(p, "Roles")

    def join_shot() -> None:
        scroll_to(page, "input[name='visibility[user_role][roles][anonymous]']", 300)
        snap("14-visibility-roles")

    place_block(page, url, f"block_content:{uuid}", "sidebar", "olivero_join_the_club", setup=join, shot=join_shot)
    # Join the club above Next hikes.
    drush_php(site, "\\Drupal\\block\\Entity\\Block::load('olivero_join_the_club')->setWeight(-10)->save();")
    visitor_shot(page, site, "/hikes/turnhouse-hill", "14-sidebar-visitor", full=True)
    visitor_shot(page, site, "/about", "14-footer", element="footer.site-footer")


def menus14_reset(site: dict) -> None:
    """The site as the blocks part of Chapter 14 leaves it: no footer menu block, footer links, Hike archive link or Privacy page; Hikes not expanded."""
    drush_php(site, """$et = \\Drupal::entityTypeManager();
$et->getStorage('block')->load('olivero_footer')?->delete();
foreach ($et->getStorage('menu_link_content')->loadByProperties(['menu_name' => 'footer']) as $l) { $l->delete(); }
foreach ($et->getStorage('menu_link_content')->loadByProperties(['title' => 'Hike archive']) as $l) { $l->delete(); }
foreach ($et->getStorage('node')->loadByProperties(['title' => 'Privacy']) as $n) { $n->delete(); }
$v = \\Drupal\\views\\Entity\\View::load('hikes'); $d = $v->get('display'); $d['page_1']['display_options']['menu']['expanded'] = FALSE; $v->set('display', $d); $v->save();
\\Drupal::service('menu_link.static.overrides')->deleteMultipleOverrides(['standard.front_page']);
\\Drupal::service('plugin.manager.menu.link')->rebuild();
drupal_flush_all_caches();""")


def menus14_steps(page: Page, site: dict, snap) -> None:
    """Chapter 14, part 3: menus. Sorts the main menu, nests a link, fills the footer menu and places it. After blocks14_content_steps."""
    url = site["url"]
    menus14_reset(site)
    views_admin_shot(page, url, "/admin/structure/menu", "14-menus", full=False)

    # Sort the main menu: Home, Hikes, Albums, About, Join us.
    # (The book drags the rows; the script sets the weights. The views links keep theirs in the view.)
    drush_php(site, """$et = \\Drupal::entityTypeManager();
foreach ($et->getStorage('menu_link_content')->loadByProperties(['menu_name' => 'main']) as $l) { $l->set('weight', $l->getTitle() == 'About' ? 3 : 4)->save(); }
foreach (['hikes' => 1, 'albums' => 2] as $id => $w) { $v = \\Drupal\\views\\Entity\\View::load($id); $d = $v->get('display'); $d['page_1']['display_options']['menu']['weight'] = $w; $v->set('display', $d); $v->save(); }
\\Drupal::service('plugin.manager.menu.link')->rebuild();
drupal_flush_all_caches();""")
    page.goto(url + "/admin/structure/menu/manage/main")
    page.wait_for_load_state("networkidle")
    row_weights(page, False)
    page.wait_for_timeout(500)
    snap("14-main-menu")

    # Hike archive, under Hikes.
    page.goto(url + "/admin/structure/menu/manage/main/add")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='title[0][value]']", "Hike archive")
    page.fill("input[name='link[0][uri]']", "/hikes/archive")
    page.select_option("select[name='menu_parent']", "main:views_view:views.hikes.page_1")
    page.wait_for_timeout(500)
    snap("14-add-link")
    page.click("input[value='Save']")
    page.wait_for_load_state("networkidle")

    # Hikes: show as expanded, so the dropdown appears.
    page.goto(url + "/admin/structure/menu/link/views_view:views.hikes.page_1/edit")
    page.wait_for_load_state("networkidle")
    page.evaluate("() => document.querySelectorAll('form details').forEach(d => d.open = true)")
    page.wait_for_timeout(300)
    page.check("input[name='expanded']")
    page.wait_for_timeout(500)
    snap("14-expanded")
    page.click("input[value='Save']")
    page.wait_for_load_state("networkidle")
    drush_php(site, "drupal_flush_all_caches();")
    visitor_shot(page, site, "/about", "14-dropdown", hover="#block-olivero-main-menu li.primary-nav__menu-item--has-children")

    # A Privacy page, for the footer.
    page.goto(url + "/node/add/page")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='title[0][value]']", "Privacy")
    page.evaluate("h => [...document.querySelectorAll('.ck-editor__editable')].pop().ckeditorInstance.setData(h)",
                  "<p>Lens &amp; Trail keeps only what it needs to run the club: your name and email address if you join, and the photos you choose to share. We never sell or pass on your details.</p>")
    page.evaluate("() => document.querySelectorAll('form details').forEach(d => d.open = true)")
    page.wait_for_timeout(300)
    page.fill("input[name='path[0][alias]']", "/privacy")
    # Basic pages go through the Editorial workflow (Chapter 6).
    page.select_option("select[name='moderation_state[0][state]']", "published")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    # The footer menu: Privacy and the hikes feed.
    for title, uri in (("Privacy", "/privacy"), ("Upcoming hikes (RSS)", "/hikes/feed")):
        page.goto(url + "/admin/structure/menu/manage/footer/add")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='title[0][value]']", title)
        page.fill("input[name='link[0][uri]']", uri)
        page.click("input[value='Save']")
        page.wait_for_load_state("networkidle")
    page.goto(url + "/admin/structure/menu/manage/footer")
    page.wait_for_load_state("networkidle")
    snap("14-footer-menu")

    # The Footer menu block, in Footer Bottom.
    place_block(page, url, "system_menu_block:footer", "footer_bottom", "olivero_footer", show_label=False)
    visitor_shot(page, site, "/about", "14-footer-menu-visitor", element="footer.site-footer")

    # The breadcrumb, deep in the hike archive.
    visitor_shot(page, site, "/hikes/archive/202612", "14-breadcrumb")


def cms_page_template_steps(page: Page, site: dict, snap) -> None:
    """Chapter 14, On Drupal CMS: the Mercury theme's page template in Canvas, with its layers."""
    page.goto(site["url"] + "/canvas")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(4000)
    page.locator("button[aria-label*='emplate']").first.click()
    page.wait_for_timeout(2500)
    page.get_by_text("Mercury theme").first.click()
    page.wait_for_timeout(6000)
    page.click("button[aria-label='Layers']")
    page.wait_for_timeout(2000)
    snap("14-cms-page-template")


def cms_easy_breadcrumb_steps(page: Page, site: dict, snap) -> None:
    """Chapter 14: Easy Breadcrumb's settings on Drupal CMS (looks only)."""
    page.goto(site["url"] + "/admin/config/user-interface/easy-breadcrumb")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    snap("14-cms-easy-breadcrumb")


# Chapter 15: users, roles and permissions.

ROLES15 = [("member", "Member"), ("hike_leader", "Hike leader"), ("secretary", "Secretary")]
PERMS15 = {
    "member": ["skip comment approval", "create gallery content", "edit own gallery content", "delete own gallery content",
               "create image media", "edit own image media", "access user profiles"],
    "hike_leader": ["create hike content", "edit own hike content", "use editorial transition create_new_draft",
                    "view own unpublished content", "view latest version", "access content overview",
                    "access navigation", "view the administration theme"],
    "secretary": ["create news content", "edit any news content", "delete own news content", "edit any hike content",
                  "edit any page content", "edit any gallery content", "use editorial transition create_new_draft",
                  "use editorial transition publish", "use editorial transition archive",
                  "use editorial transition archived_draft", "use editorial transition archived_published",
                  "view any unpublished content", "view latest version", "access content overview", "administer comments",
                  "administer users", "edit any club_info block content", "access navigation",
                  "view the administration theme", "access administration pages"],
}
USERS15 = [("morag", "morag@example.com", ["member", "secretary"]), ("jordi", "jordi@example.com", ["member", "hike_leader"]),
           ("ailsa", "ailsa@example.com", ["member"])]
MAILPIT = "https://lens-and-trail.ddev.site:8026"


def users15_reset(site: dict) -> None:
    """The site as Chapter 14 leaves it: only admin, Drupal's four roles, registration by administrators only, no CAPTCHA."""
    drush_php(site, """$et = \\Drupal::entityTypeManager();
foreach ($et->getStorage('user')->loadMultiple() as $u) { if ($u->id() > 1) { $u->delete(); } }
foreach (['member', 'hike_leader', 'secretary'] as $r) { \\Drupal\\user\\Entity\\Role::load($r)?->delete(); }
\\Drupal\\user\\Entity\\Role::load('authenticated')->grantPermission('skip comment approval')->save();
foreach (['field_camera', 'field_about_me'] as $f) { \\Drupal\\field\\Entity\\FieldStorageConfig::loadByName('user', $f)?->delete(); }
// Purge the deleted fields now. If cron purges them after the chapter has made new fields with the same names, a core bug
// deletes the new fields' schema records ("Mismatched entity and/or field definitions"; see PROJECT-LOG).
field_purge_batch(1000);
foreach ($et->getStorage('comment')->loadMultiple() as $c) { $c->delete(); }
foreach ($et->getStorage('node')->loadByProperties(['title' => 'Arthur\\'s Seat by night']) as $n) { $n->delete(); }
\\Drupal::configFactory()->getEditable('user.settings')->set('register', 'admin_only')->save();
$f = \\Drupal\\field\\Entity\\FieldConfig::loadByName('node', 'hike', 'field_hike_leader'); $h = $f->getSetting('handler_settings'); $h['filter'] = ['type' => '_none']; $f->setSetting('handler_settings', $h)->save();""")
    uninstall(site, "image_captcha", "captcha")
    try:
        subprocess.run(["curl", "-sk", "-X", "DELETE", MAILPIT + "/api/v1/messages"], check=True, capture_output=True)
    except Exception:
        pass


def as_user(page: Page, site: dict, name: str, password: str = "12345"):
    """A window of its own, logged in as someone else. Returns (context, page); close the context afterwards."""
    context = page.context.browser.new_context(viewport={"width": WIDTH, "height": 1000}, device_scale_factor=2, ignore_https_errors=True)
    other = context.new_page()
    log_in(other, {**site, "user": name, "password": password})
    return context, other


def permissions_filter(page: Page, text: str) -> None:
    page.locator("input[type='search']").first.press_sequentially(text, delay=60)
    page.mouse.move(5, 5)
    page.wait_for_timeout(1500)


def users15_roles_steps(page: Page, site: dict, snap) -> None:
    """Chapter 15, part 1: the People page, the club's roles and their permissions, and the club's first accounts."""
    url = site["url"]
    users15_reset(site)
    views_admin_shot(page, url, "/admin/people", "15-people", full=False)

    # Three roles.
    for machine, label in ROLES15:
        page.goto(url + "/admin/people/roles/add")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='label']", label)
        page.wait_for_timeout(1500)
        if machine == "member":
            snap("15-add-role")
        page.click("#edit-submit")
        page.wait_for_load_state("networkidle")
    # Least permissive first (the book drags the rows).
    order = ["anonymous", "authenticated", "member", "hike_leader", "secretary", "content_editor", "administrator"]
    drush_php(site, "foreach (" + repr(order).replace("'", '"') + " as $w => $r) { \\Drupal\\user\\Entity\\Role::load($r)->setWeight($w)->save(); }")
    views_admin_shot(page, url, "/admin/people/roles", "15-roles", full=False)

    # Authenticated users' comments wait for approval; members' don't.
    page.goto(url + "/admin/people/permissions/authenticated")
    page.wait_for_load_state("networkidle")
    page.uncheck("input[name='authenticated[skip comment approval]']")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    for role, permissions in PERMS15.items():
        page.goto(url + f"/admin/people/permissions/{role}")
        page.wait_for_load_state("networkidle")
        for permission in permissions:
            page.check(f"input[name='{role}[{permission}]']")
        if role == "member":
            permissions_filter(page, "comment")
            snap("15-permissions-member")
        if role == "hike_leader":
            permissions_filter(page, "editorial")
            snap("15-permissions-transitions")
        page.click("#edit-submit")
        page.wait_for_load_state("networkidle")
    page.goto(url + "/admin/people/permissions")
    page.wait_for_load_state("networkidle")
    permissions_filter(page, "hike")
    snap("15-permissions-all")

    # The club's first accounts: the secretary through the form, the others alike.
    for name, mail, roles in USERS15:
        page.goto(url + "/admin/people/create")
        page.wait_for_load_state("networkidle")
        page.fill("input[name='mail']", mail)
        page.fill("input[name='name']", name)
        for role in roles:
            page.check(f"input[name='roles[{role}]']")
        if name == "morag":
            page.wait_for_timeout(500)
            snap("15-add-user")
        page.click("#edit-submit")
        page.wait_for_load_state("networkidle")
    # The script knows their passwords; they would set their own from the email.
    for name, _, _ in USERS15:
        drush(site, "user:password", name, "12345")
    views_admin_shot(page, url, "/admin/people", "15-people-after", full=False)


def users15_registration_steps(page: Page, site: dict, snap) -> None:
    """Chapter 15, part 2: registration with approval, the email, activating an account, and a comment waiting for approval. After users15_roles_steps."""
    url = site["url"]
    page.goto(url + "/admin/config/people/accounts")
    page.wait_for_load_state("networkidle")
    page.check("input[name='user_register'][value='visitors_admin_approval']")
    page.wait_for_timeout(500)
    scroll_to(page, "input[name='user_register'][value='admin_only']", 200)
    snap("15-account-settings")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    # A visitor registers.
    context = page.context.browser.new_context(viewport={"width": WIDTH, "height": 1000}, device_scale_factor=2, ignore_https_errors=True)
    visit = context.new_page()
    visit.goto(url + "/user/register")
    visit.wait_for_load_state("networkidle")
    visit.fill("input[name='mail']", "lucia@example.com")
    visit.fill("input[name='name']", "lucia")
    visit.wait_for_timeout(500)
    save(visit, "15-register", full_page=True)
    visit.click("#edit-submit")
    visit.wait_for_load_state("networkidle")
    save(visit, "15-register-done")
    context.close()

    # The secretary's mailbox: Mailpit catches everything the site sends.
    page.wait_for_timeout(2000)
    page.goto(MAILPIT)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    # Two emails: one to the visitor, one to the club's address. Open the club's.
    page.locator(".message:has-text('hello@lens-and-trail'), a:has-text('pending admin approval'):has-text('hello@')").first.click()
    page.wait_for_timeout(2000)
    snap("15-mailpit")

    # The secretary activates the account; the admin gives the role.
    page.goto(url + "/admin/people")
    page.wait_for_load_state("networkidle")
    snap("15-people-blocked")
    lucia = drush_php(site, "echo current(\\Drupal::entityTypeManager()->getStorage('user')->loadByProperties(['name' => 'lucia']))->id();").strip()
    context, secretary = as_user(page, site, "morag")
    secretary.goto(url + f"/user/{lucia}/edit")
    secretary.wait_for_load_state("networkidle")
    secretary.check("input[name='status'][value='1']")
    secretary.wait_for_timeout(500)
    scroll_to(secretary, "input[name='status'][value='1']", 300)
    save(secretary, "15-activate")
    secretary.click("#edit-submit")
    secretary.wait_for_load_state("networkidle")
    context.close()
    drush(site, "user:password", "lucia", "12345")

    # Lucía isn't a member yet: her comment waits.
    context, lucia_page = as_user(page, site, "lucia")
    lucia_page.goto(url + "/node/11")
    lucia_page.wait_for_load_state("networkidle")
    lucia_page.evaluate("h => [...document.querySelectorAll('.ck-editor__editable')].pop().ckeditorInstance.setData(h)",
                        "<p>Lovely light on the Turnhouse photo! Which lens was that?</p>")
    lucia_page.click("form.comment-form input[value='Save'], form.comment-form #edit-submit")
    lucia_page.wait_for_load_state("networkidle")
    context.close()
    views_admin_shot(page, url, "/admin/content/comment/approval", "15-unapproved", full=False)

    # The admin makes her a member: the bulk action on People.
    page.goto(url + "/admin/people")
    page.wait_for_load_state("networkidle")
    page.locator("tr:has-text('lucia') input[type='checkbox']").first.check()
    page.wait_for_timeout(800)
    page.select_option("select[name='action']", "user_add_role_action.member")
    page.wait_for_timeout(500)
    snap("15-bulk-role")
    page.locator("input[value='Apply to selected items']").first.click()
    page.wait_for_load_state("networkidle")



def users15_captcha_steps(page: Page, site: dict, snap) -> None:
    """Chapter 15, part 3: CAPTCHA on the registration and password forms. After users15_registration_steps."""
    url = site["url"]
    uninstall(site, "image_captcha", "captcha")
    # Downloaded with Composer, as in Chapter 11.
    composer(site, "require", "drupal/captcha")
    page.goto(url + "/admin/modules")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    page.fill("input[name='text']", "captcha")
    page.wait_for_timeout(1000)
    page.check("input[name='modules[captcha][enable]']")
    page.check("input[name='modules[image_captcha][enable]']")
    page.wait_for_timeout(500)
    snap("15-extend-captcha")
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")

    page.goto(url + "/admin/config/people/captcha")
    page.wait_for_load_state("networkidle")
    page.select_option("select[name='default_challenge']", "image_captcha/Image")
    page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    # The forms to protect: registration and the password reset.
    for form in ("user_register_form", "user_pass"):
        drush_php(site, f"$p = \\Drupal\\captcha\\Entity\\CaptchaPoint::load('{form}'); $p->enable()->save();")
    views_admin_shot(page, url, "/admin/config/people/captcha/captcha-points", "15-captcha-points", full=False)
    as_visitor(page, site, "/user/register", "15-register-captcha")


def users15_more_steps(page: Page, site: dict, snap) -> None:
    """Chapter 15, part 4: user fields and a profile, time zones, the Hike leader field, and a hike from draft to published. After users15_captcha_steps."""
    url = site["url"]
    fields = url + "/admin/config/people/accounts/fields"
    create_field(page, fields, "Plain text", "Camera", "Short text")
    create_field(page, fields, "Plain text", "About me", "Long text")
    page.goto(fields)
    page.wait_for_load_state("networkidle")
    snap("15-user-fields")
    drush_php(site, """$u = current(\\Drupal::entityTypeManager()->getStorage('user')->loadByProperties(['name' => 'jordi']));
$u->set('field_camera', 'Fujifilm X-T5, and a phone when it rains')->set('field_about_me', "I moved to Edinburgh from Barcelona in 2019, and I've been leading hikes in the Pentlands ever since. Ask me about the best spots for sunrise.")->save();""")
    jordi = drush_php(site, "echo current(\\Drupal::entityTypeManager()->getStorage('user')->loadByProperties(['name' => 'jordi']))->id();").strip()
    context, member = as_user(page, site, "ailsa")
    member.goto(url + f"/user/{jordi}")
    member.wait_for_load_state("networkidle")
    save(member, "15-profile")
    context.close()

    # Time zones.
    page.goto(url + "/admin/config/regional/settings")
    page.wait_for_load_state("networkidle")
    scroll_to(page, "input[name='configurable_timezones']", 250)
    snap("15-timezones")

    # Only hike leaders in the Hike leader field.
    page.goto(url + "/admin/structure/types/manage/hike/fields/node.hike.field_hike_leader")
    page.wait_for_load_state("networkidle")
    page.select_option("select[name='settings[handler_settings][filter][type]']", "role")
    page.wait_for_timeout(2500)
    page.check("input[name='settings[handler_settings][filter][role][hike_leader]']")
    page.wait_for_timeout(500)
    scroll_to(page, "select[name='settings[handler_settings][filter][type]']", 250)
    snap("15-hike-leader-field")
    page.locator("input[value='Save settings'], button:has-text('Save settings')").first.click()
    page.wait_for_load_state("networkidle")

    # The Try it: hikes with admin as their leader get Jordi (admin isn't a
    # hike leader, so these references would fail the next time they're saved).
    drush_php(site, """$jordi = current(\\Drupal::entityTypeManager()->getStorage('user')->loadByProperties(['name' => 'jordi']));
foreach (\\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['type' => 'hike', 'field_hike_leader' => 1]) as $hike) {
  $hike->set('field_hike_leader', $jordi->id())->setNewRevision(TRUE);
  $hike->setRevisionLogMessage('Jordi leads this hike.');
  $hike->save();
}""")

    # Jordi writes a hike: he can only save it as a draft.
    context, leader = as_user(page, site, "jordi")
    leader.goto(url + "/node/add/hike")
    leader.wait_for_load_state("networkidle")
    leader.fill("input[name='title[0][value]']", "Arthur's Seat by night")
    leader.fill("input[name='field_date[0][value][date]']", "2027-01-16")
    leader.fill("input[name='field_date[0][value][time]']", "17:30:00")
    leader.fill("input[name='field_meeting_place[0][value]']", "Holyrood Park, St Margaret's Loch car park")
    leader.fill("input[name='field_distance[0][value]']", "5")
    leader.check("input[name='field_difficulty'][value='moderate']")
    leader.select_option("select[name='field_hike_leader']", label="jordi")
    leader.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    leader.wait_for_timeout(500)
    leader.locator("select[name='moderation_state[0][state]']").scroll_into_view_if_needed()
    save(leader, "15-leader-draft")
    leader.click("#edit-submit")
    leader.wait_for_load_state("networkidle")
    context.close()

    # Morag, the secretary, publishes it.
    node = drush_php(site, "echo current(\\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => 'Arthur\\'s Seat by night']))->id();").strip()
    context, secretary = as_user(page, site, "morag")
    secretary.goto(url + "/admin/content")
    secretary.wait_for_load_state("networkidle")
    save(secretary, "15-secretary-content")
    secretary.goto(url + f"/node/{node}/edit")
    secretary.wait_for_load_state("networkidle")
    secretary.select_option("select[name='moderation_state[0][state]']", "published")
    secretary.locator("select[name='moderation_state[0][state]']").scroll_into_view_if_needed()
    secretary.wait_for_timeout(500)
    save(secretary, "15-secretary-publish")
    secretary.click("#edit-submit")
    secretary.wait_for_load_state("networkidle")
    context.close()


def members15_undo(site: dict) -> None:
    """Appendix C, Exercise 15.7: remove the Members' corner view and block."""
    drush_php(site, """\\Drupal\\views\\Entity\\View::load('members_corner')?->delete();
foreach (\\Drupal::entityTypeManager()->getStorage('block_content')->loadByProperties(['info' => "Members' corner"]) as $b) { $b->delete(); }""")


def members15_steps(page: Page, site: dict, snap) -> None:
    """Appendix C, the answer to Exercise 15.7: a Members' corner at /members (after the Chapter 15 sequences; undone at the end)."""
    url = site["url"]
    members15_undo(site)
    # The text, in a reusable Basic block that isn't placed anywhere.
    page.goto(url + "/block/add/basic")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='info[0][value]']", "Members' corner")
    page.evaluate("h => [...document.querySelectorAll('.ck-editor__editable')].pop().ckeditorInstance.setData(h)",
                  "<p><strong>Photo evenings</strong> are in the back room of the Shore Café, 12 Water Street, Leith. Ring the bell if the door is closed.</p>"
                  "<p><strong>On a hike and running late?</strong> Call or text the secretary: 07700 900123.</p>"
                  "<p>The club's shared album for 2027 is open: ask Morag for the link.</p>")
    page.wait_for_timeout(1000)
    snap("appendix-c-members-block")
    page.locator("#edit-actions input[value='Save'], #edit-submit").first.click()
    page.wait_for_load_state("networkidle")
    # A view of content blocks, with a page at /members.
    views_new(page, url, "Members' corner", [
        ("show[wizard_key]", "block_content"),
        ("page[create]", True),
        ("page[title]", "Members' corner"),
        ("page[path]", "members"),
        ("page[items_per_page]", "1"),
    ])
    page.goto(url + "/admin/structure/views/view/members_corner/edit/page_1")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    # Only this block: a filter on its description.
    views_add(page, "members_corner/page_1/filter", "Block description", "block_content_field_data.info")
    page.fill(".ui-dialog input[name='options[value]']", "Members' corner")
    views_apply(page)
    # Show the block as it is, not as fields.
    views_dialog(page, "display/members_corner/page_1/row")
    page.check(".ui-dialog input[name='row[type]'][value='entity:block_content']")
    views_apply(page)
    # The row style's settings (the view mode), if Views asks for them.
    if page.locator(".ui-dialog-buttonpane button:has-text('Apply')").count():
        views_apply(page)
    # Members only.
    views_dialog(page, "display/members_corner/page_1/access")
    page.check(".ui-dialog input[name='access[type]'][value='role']")
    views_apply(page)
    page.check(".ui-dialog input[name='access_options[role][member]']")
    page.wait_for_timeout(500)
    snap("appendix-c-members-access", element=".ui-dialog")
    views_apply(page)
    page.mouse.move(1200, 600)
    page.wait_for_timeout(800)
    snap("appendix-c-members-view")
    views_save(page)
    context, other = as_user(page, site, "ailsa")
    other.goto(url + "/members")
    other.wait_for_load_state("networkidle")
    other.wait_for_timeout(800)
    save(other, "appendix-c-members-page")
    context.close()
    as_visitor(page, site, "/members", "appendix-c-members-denied")
    members15_undo(site)


# Chapter 16: themes.

LOGO16 = ROOT / "examples" / "club" / "lens-and-trail-logo.svg"


def theme_link(page: Page, url: str, theme: str, action: str = "default") -> None:
    """Appearance: select a theme's Install / Set as default link (action: install or default)."""
    page.goto(url + "/admin/appearance")
    page.wait_for_load_state("networkidle")
    with page.expect_navigation():
        page.locator(f"a[href^='/admin/appearance/{action}?theme={theme}&']").first.evaluate("e => e.click()")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)


def themes16_reset(site: dict) -> None:
    drush_php(site, """\\Drupal::configFactory()->getEditable('system.theme')->set('default', 'olivero')->save();
\\Drupal::configFactory()->getEditable('olivero.settings')->set('base_primary_color', '#1b9ae4')->set('site_branding_bg_color', 'default')->set('mobile_menu_all_widths', 0)->set('logo.use_default', FALSE)->clear('logo.path')->save();
\\Drupal::configFactory()->getEditable('system.theme.global')->set('features.node_user_picture', TRUE)->save();
$installed = \\Drupal::service('theme_handler')->listInfo();
$gone = array_values(array_intersect(['stark', 'solo'], array_keys($installed)));
if ($gone) { \\Drupal::service('theme_installer')->uninstall($gone); }
\\Drupal::configFactory()->getEditable('system.development')->set('twig_debug', FALSE)->set('twig_cache_disable', FALSE)->save();""")
    drush(site, "cache:rebuild")


def themes16_steps(page: Page, site: dict, snap) -> None:
    """Chapter 16 on core: Appearance, Stark, Solo from drupal.org, back to Olivero, Olivero's settings, the admin theme."""
    url = site["url"]
    themes16_reset(site)
    page.goto(url + "/admin/appearance")
    page.wait_for_load_state("networkidle")
    page.set_viewport_size({"width": WIDTH, "height": page.evaluate("document.documentElement.scrollHeight")})
    page.wait_for_timeout(1000)
    snap("16-appearance")
    page.set_viewport_size({"width": WIDTH, "height": 1000})
    # Stark: what Drupal looks like without a theme's styling.
    theme_link(page, url, "stark")
    as_visitor(page, site, "/", "16-stark")
    # A theme from drupal.org: Solo.
    composer(site, "require", "drupal/solo")
    page.goto(url + "/admin/appearance")
    page.wait_for_load_state("networkidle")
    scroll_to(page, "h3:has-text('Solo')")
    snap("16-appearance-solo")
    theme_link(page, url, "solo")
    as_visitor(page, site, "/", "16-solo")
    page.goto(url + "/admin/appearance/settings/solo")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(800)
    snap("16-solo-settings")
    page.goto(url + "/admin/structure/block/list/solo")
    page.wait_for_load_state("networkidle")
    page.set_viewport_size({"width": WIDTH, "height": 1500})
    page.wait_for_timeout(1000)
    snap("16-solo-blocks")
    page.set_viewport_size({"width": WIDTH, "height": 1000})
    # Back to Olivero, and Solo and Stark out again.
    theme_link(page, url, "olivero")
    page.goto(url + "/admin/appearance")
    page.wait_for_load_state("networkidle")
    for theme in ["solo", "stark"]:
        page.goto(url + f"/admin/appearance/uninstall?theme={theme}")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(800)
        if theme == "solo":
            if page.locator("details").first.get_attribute("open") is None:
                page.locator("details summary").first.click()
                page.wait_for_timeout(500)
            snap("16-uninstall-solo")
        with page.expect_navigation():
            page.click("input[value='Uninstall']")
        page.wait_for_load_state("networkidle")
    composer(site, "remove", "drupal/solo")
    # Olivero's settings: the club's colour and logo.
    page.goto(url + "/admin/appearance/settings/olivero")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    snap("16-olivero-global")
    scroll_to(page, "text=Olivero Utilities")
    page.wait_for_timeout(500)
    page.fill("input[name='base_primary_color']", "#1f6f5c")
    page.locator("input[name='base_primary_color']").dispatch_event("change")
    page.wait_for_timeout(800)
    snap("16-olivero-color")
    scroll_to(page, "input[name='default_logo']")
    page.uncheck("input[name='default_logo']")
    page.wait_for_timeout(500)
    page.set_input_files("input[name='files[logo_upload]']", str(LOGO16))
    page.wait_for_timeout(500)
    snap("16-olivero-logo")
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    as_visitor(page, site, "/", "16-olivero-club")
    # The administration theme.
    page.goto(url + "/admin/appearance")
    page.wait_for_load_state("networkidle")
    snap("16-admin-theme", element="details:has(summary:has-text('Administration theme'))")
    views_admin_shot(page, url, "/admin/appearance/settings/default_admin", "16-default-admin-settings", full=False)


def themes16_cms_reset(site: dict) -> None:
    drush_php(site, """\\Drupal::configFactory()->getEditable('system.theme')->set('default', 'mercury')->save();
$installed = \\Drupal::service('theme_handler')->listInfo();
$gone = array_values(array_intersect(['olivero', 'tara', 'byte_theme'], array_keys($installed)));
if ($gone) { \\Drupal::service('theme_installer')->uninstall($gone); }""")
    drush(site, "cache:rebuild")


def themes16_cms_steps(page: Page, site: dict, snap) -> None:
    """Chapter 16 on Drupal CMS: Mercury and its settings, then the same site in Olivero, Tara and Byte."""
    url = site["url"]
    themes16_cms_reset(site)
    views_admin_shot(page, url, "/admin/appearance", "16-cms-appearance", full=False)
    views_admin_shot(page, url, "/admin/appearance/settings/mercury", "16-cms-mercury-settings", full=False)
    as_visitor(page, site, "/join", "16-cms-mercury")
    composer(site, "require", "drupal/tara", "drupal/byte_theme")
    for theme in ["olivero", "tara", "byte_theme"]:
        theme_link(page, url, theme)
        as_visitor(page, site, "/join", f"16-cms-{theme.replace('_theme', '')}")
    theme_link(page, url, "mercury")
    themes16_cms_reset(site)


def themes16_twig_steps(page: Page, site: dict, snap) -> None:
    """Chapter 16, Under the hood: templates. Twig development mode on for a screenshot, then off again."""
    url = site["url"]
    page.goto(url + "/admin/config/development/settings")
    page.wait_for_load_state("networkidle")
    page.check("input[name='twig_development_mode']")
    page.wait_for_timeout(500)
    for name in ["twig_debug", "twig_cache_disable"]:
        page.check(f"input[name='{name}']")
    page.wait_for_timeout(500)
    snap("16-development-settings")
    drush_php(site, "\\Drupal::keyValue('development_settings')->deleteAll();")
    drush(site, "cache:rebuild")


# Chapter 17: nice URLs and SEO.

SEO17_MODULES = ["simple_sitemap", "redirect_404", "redirect", "pathauto"]
SEO17_ALIASES = ["/about", "/join", "/welcome", "/hikes/turnhouse-hill", "/privacy"]


def seo17_reset(site: dict) -> None:
    """Back to Chapter 16: no Pathauto, Redirect or sitemap; only the hand-made aliases; the Glencorse hike's old title."""
    drush_php(site, """$installed = array_keys(\\Drupal::moduleHandler()->getModuleList());
$gone = array_values(array_intersect(%s, $installed));
if (in_array('redirect', $gone)) { $r = \\Drupal::entityTypeManager()->getStorage('redirect'); $r->delete($r->loadMultiple()); }
if ($gone) { \\Drupal::service('module_installer')->uninstall($gone); }
$storage = \\Drupal::entityTypeManager()->getStorage('path_alias');
foreach ($storage->loadMultiple() as $a) { if (!in_array($a->getAlias(), %s)) { $a->delete(); } }
foreach (\\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => 'Glencorse Reservoir winter loop']) as $n) { $n->setTitle('Glencorse Reservoir loop'); $n->setNewRevision(FALSE); $n->save(); }""" % (php_list(SEO17_MODULES), php_list(SEO17_ALIASES)))
    drush(site, "cache:rebuild")


def php_list(items: list[str]) -> str:
    return "[" + ", ".join(php_str(i) for i in items) + "]"


def add_pattern(page: Page, url: str, kind: str, pattern: str, bundles: list[str], label: str, shot=None) -> None:
    page.goto(url + "/admin/config/search/path/patterns/add")
    page.wait_for_load_state("networkidle")
    page.select_option("select[name='type']", kind)
    page.wait_for_selector("input[name='pattern']")
    page.wait_for_timeout(1500)
    page.fill("input[name='pattern']", pattern)
    for b in bundles:
        page.check(f"input[name='bundles[{b}]']")
    page.fill("input[name='label']", label)
    page.wait_for_timeout(1500)  # The machine name follows the label.
    if shot:
        shot()
    with page.expect_navigation():
        page.click("input[value='Save']")
    page.wait_for_load_state("networkidle")


def keep_alias17(page: Page, site: dict, title: str) -> None:
    """Unticks Generate automatic URL alias on a node, so Pathauto leaves its hand-made alias alone."""
    nid = drush_php(site, f"echo array_key_first(\\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => {php_str(title)}]));").strip()
    page.goto(site["url"] + f"/node/{nid}/edit")
    page.wait_for_load_state("networkidle")
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    page.uncheck("input[name='path[0][pathauto]']")
    if page.locator("select[name='moderation_state[0][state]']").count():
        page.select_option("select[name='moderation_state[0][state]']", "published")
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")


def seo17_steps(page: Page, site: dict, snap) -> None:
    """Chapter 17 on core: Pathauto patterns and bulk aliases, Redirect and Redirect 404, Simple XML Sitemap."""
    url = site["url"]
    seo17_reset(site)
    composer(site, "require", "drupal/pathauto", "drupal/redirect", "drupal/simple_sitemap")
    page.goto(url + "/admin/modules")
    page.wait_for_load_state("networkidle")
    page.fill("input[name='text']", "path")
    page.wait_for_timeout(800)
    page.fill("input[name='text']", "")
    for m in ["pathauto", "redirect", "redirect_404", "simple_sitemap"]:
        page.check(f"input[name='modules[{m}][enable]']")
    page.wait_for_timeout(500)
    scroll_to(page, "input[name='modules[pathauto][enable]']")
    snap("17-extend")
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    if page.locator("input[value='Continue']").count():
        with page.expect_navigation():
            page.click("input[value='Continue']")
        page.wait_for_load_state("networkidle")
    # Patterns.
    def token_browser() -> None:
        page.click("a:has-text('Browse available tokens.')")
        page.wait_for_selector(".ui-dialog .token-tree, .ui-dialog table", timeout=20000)
        page.wait_for_timeout(1500)
        page.locator(".ui-dialog tr:has-text('Nodes') .token-tree-toggle, .ui-dialog tr:has-text('Nodes') a").first.click()
        page.wait_for_timeout(1500)
        snap("17-token-browser", element=".ui-dialog")
        page.click(".ui-dialog-titlebar-close")
        page.wait_for_timeout(500)
        snap("17-pattern-hike")

    add_pattern(page, url, "canonical_entities:node", "/hikes/[node:title]", ["hike"], "Hikes", token_browser)
    add_pattern(page, url, "canonical_entities:node", "/galleries/[node:title]", ["gallery"], "Albums")
    add_pattern(page, url, "canonical_entities:node", "/news/[node:title]", ["news"], "News")

    def areas() -> None:
        snap("17-pattern-areas")

    add_pattern(page, url, "canonical_entities:taxonomy_term", "/areas/[term:parents:join-path]/[term:name]", ["areas"], "Areas", areas)
    add_pattern(page, url, "canonical_entities:taxonomy_term", "/photo-themes/[term:name]", ["photo_themes"], "Photo themes")
    views_admin_shot(page, url, "/admin/config/search/path/patterns", "17-patterns", full=False)
    page.goto(url + "/admin/config/search/path/settings")
    page.wait_for_load_state("networkidle")
    scroll_to(page, "input[name='update_action']", offset=300)
    snap("17-pathauto-settings")
    # Aliases for everything that has none yet.
    page.goto(url + "/admin/config/search/path/update_bulk")
    page.wait_for_load_state("networkidle")
    page.check("input[name='update[canonical_entities:node]']")
    page.check("input[name='update[canonical_entities:taxonomy_term]']")
    page.wait_for_timeout(300)
    snap("17-bulk")
    page.click("input[value='Update']")
    page.wait_for_url("**/update_bulk*", timeout=120000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    page.goto(url + "/admin/config/search/path")
    page.wait_for_load_state("networkidle")
    page.set_viewport_size({"width": WIDTH, "height": page.evaluate("document.documentElement.scrollHeight")})
    page.wait_for_timeout(800)
    snap("17-aliases")
    page.set_viewport_size({"width": WIDTH, "height": 1000})
    as_visitor(page, site, "/areas/pentland-hills/turnhouse-hill", "17-term-alias")
    # A hike's alias on its form.
    nid = drush_php(site, "echo array_key_first(\\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => 'Glencorse Reservoir loop']));").strip()
    page.goto(url + f"/node/{nid}/edit")
    page.wait_for_load_state("networkidle")
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    page.wait_for_timeout(500)
    snap("17-hike-alias", element="details:has(input[name='path[0][pathauto]'])")
    # Keep the Turnhouse hike's hand-made alias: untick Generate automatic URL alias, and save.
    keep_alias17(page, site, "Turnhouse Hill and Carnethy Hill")
    page.goto(url + f"/node/{nid}/edit")
    page.wait_for_load_state("networkidle")
    # Rename the hike: Pathauto makes a new alias, Redirect keeps the old one working.
    page.fill("input[name='title[0][value]']", "Glencorse Reservoir winter loop")
    if page.locator("select[name='moderation_state[0][state]']").count():
        page.select_option("select[name='moderation_state[0][state]']", "published")
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    views_admin_shot(page, url, "/admin/config/search/redirect", "17-redirects", full=False)
    # Redirect 404: an address that doesn't exist.
    for path in ["/hikes/arthurs-seat", "/hikes/arthurs-seat", "/gallery"]:
        context = page.context.browser.new_context(ignore_https_errors=True)
        context.new_page().goto(url + path)
        context.close()
    views_admin_shot(page, url, "/admin/config/search/redirect/404", "17-404", full=False)
    # The sitemap.
    page.goto(url + "/admin/config/search/simplesitemap/entities/node")
    page.wait_for_load_state("networkidle")
    for b, label in [("hike", "Hike"), ("gallery", "Gallery"), ("news", "News"), ("page", "Basic page")]:
        page.locator(f".vertical-tabs__menu a:has-text('{label}'), .vertical-tabs__menu-item a:has-text('{label}')").first.click()
        page.wait_for_timeout(500)
        page.evaluate(f"document.querySelector('#edit-bundles-{b}-default').open = true")
        page.wait_for_timeout(500)
        page.locator(f"label[for='edit-bundles-{b}-default-index-1']").click()
        if b == "hike":
            page.wait_for_timeout(400)
            snap("17-sitemap-settings")
    page.check("input[name='simple_sitemap_regenerate_now']")
    with page.expect_navigation():
        page.click("input[value='Save configuration']")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)
    as_visitor(page, site, "/sitemap.xml", "17-sitemap")


# Chapter 17 on Drupal CMS: Metatag, Real-time SEO and the SEO Checklist.

SEO17_TIPS = "Taking photos on a hike"
SEO17_TIPS_BODY = ("<p>Hiking photography is about travelling light and stopping often. Here are the tips we share with new members "
                   "before their first hike with the club.</p><h2>Pack light</h2><p>One camera body and one zoom lens are enough for "
                   "a day in the Pentland Hills. A phone is a fine second camera.</p><h2>Shoot the light</h2><p>Early starts give the "
                   "best light on Glencorse Reservoir. On a grey day, look for details: frost on a gate, a burn in the snow.</p>"
                   "<h2>Keep up with the group</h2><p>Tell the hike leader when you stop for a photo, and catch up at the next gate.</p>")


SEO17_SOCIAL_STYLES = ["social_media_facebook", "social_media_x"]


def seo17_cms_reset(site: dict) -> None:
    drush_php(site, f"""
foreach ({php_list(SEO17_SOCIAL_STYLES)} as $id) {{
  $style = \\Drupal\\image\\Entity\\ImageStyle::load($id);
  $has = FALSE;
  foreach ($style->getEffects() as $e) {{ if ($e->getPluginId() == 'image_convert_avif') {{ $has = TRUE; }} }}
  if (!$has) {{ $style->addImageEffect(['id' => 'image_convert_avif', 'weight' => -9, 'data' => ['extension' => 'webp']]); $style->save(); }}
  $style->flush();
}}
foreach (\\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => '{SEO17_TIPS}']) as $n) {{ $n->delete(); }}
foreach (\\Drupal::entityTypeManager()->getStorage('media')->loadByProperties(['name' => 'Glencorse Reservoir from the hillside']) as $m) {{ $m->delete(); }}
foreach (\\Drupal::entityTypeManager()->getStorage('path_alias')->loadMultiple() as $a) {{ if (str_starts_with($a->getAlias(), '/taking-photos-hike')) {{ $a->delete(); }} }}
""")


def seo17_cms_steps(page: Page, site: dict, snap) -> None:
    """Chapter 17 on Drupal CMS: Metatag defaults, a Basic page's SEO fields, Real-time SEO and the SEO Checklist."""
    url = site["url"]
    seo17_cms_reset(site)
    views_admin_shot(page, url, "/admin/config/search/path/patterns", "17-cms-patterns", full=False)
    views_admin_shot(page, url, "/admin/config/search/metatag", "17-cms-metatag", full=False)
    page.goto(url + "/admin/config/search/metatag/node")
    page.wait_for_load_state("networkidle")
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = false)")
    page.locator("summary:has-text('Open Graph')").first.click()
    page.wait_for_timeout(600)
    scroll_to(page, "summary:has-text('Open Graph')")
    snap("17-cms-metatag-node")
    # Social media images as JPEG: delete the Convert to AVIF effect from the two social media image styles.
    for style in SEO17_SOCIAL_STYLES:
        page.goto(url + f"/admin/config/media/image-styles/manage/{style}")
        page.wait_for_load_state("networkidle")
        page.goto(url + page.locator("tr:has-text('Convert to AVIF') a[href$='/delete']").first.get_attribute("href"))
        page.wait_for_load_state("networkidle")
        with page.expect_navigation():
            page.click("#edit-submit")
        page.wait_for_load_state("networkidle")
        if style == "social_media_facebook":
            page.wait_for_timeout(500)
            snap("17-cms-social-style")
    # A Basic page with a photo, made in the background; we only look at its SEO fields.
    shutil.copy(PHOTOS / "glencorse-reservoir-portrait.jpg", Path(site["dir"]) / "web/sites/default/files/glencorse-reservoir-portrait.jpg")
    nid = drush_php(site, f"""
$file = \\Drupal\\file\\Entity\\File::create(['uri' => 'public://glencorse-reservoir-portrait.jpg', 'status' => 1]);
$file->save();
$media = \\Drupal\\media\\Entity\\Media::create(['bundle' => 'image', 'name' => 'Glencorse Reservoir from the hillside',
  'field_media_image' => ['target_id' => $file->id(), 'alt' => 'Glencorse Reservoir between the hills, seen from a grassy slope with two trees']]);
$media->save();
$node = \\Drupal\\node\\Entity\\Node::create(['type' => 'page', 'title' => '{SEO17_TIPS}', 'uid' => 1,
  'field_description' => 'How the club takes photos on a hike: what to pack, when the light is best, and how to keep up with the group.',
  'field_content' => ['value' => {SEO17_TIPS_BODY!r}, 'format' => 'content_format'],
  'field_featured_image' => $media->id(), 'moderation_state' => 'published']);
$node->save();
echo $node->id();
""")
    page.goto(url + f"/node/{nid}/edit")
    page.wait_for_load_state("networkidle")
    page.locator("summary:has-text('Search Engine Optimization')").first.click()
    page.wait_for_timeout(600)
    page.fill("input[name='field_seo_analysis[0][focus_keyword]']", "hiking photography")
    page.wait_for_timeout(4000)
    scroll_to(page, "summary:has-text('Search Engine Optimization')")
    snap("17-cms-seo-fields")
    page.fill("textarea[name='field_seo_description[0][value]']", "Tips from the Lens & Trail photo club for hiking photography in the hills around Edinburgh: what to pack, when the light is best, and how to keep up with the group.")
    page.click("input[value='Seo preview']")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(4000)
    scroll_to(page, "input[name='field_seo_analysis[0][focus_keyword]']", offset=200)
    snap("17-cms-realtime-seo")
    page.select_option("select[name='moderation_state[0][state]']", "published")
    with page.expect_navigation():
        page.click("input[value='Save']")
    page.wait_for_load_state("networkidle")
    as_visitor(page, site, f"/node/{nid}", "17-cms-tips")
    views_admin_shot(page, url, "/admin/config/search/seo-checklist", "17-cms-seo-checklist", full=False)


# Chapter 18: multilingual sites. The sequences restore a database snapshot taken when Chapter 17 was done.

ES18_PAGES = {
    "About the club": ("Sobre el club", "/sobre-el-club",
        "<p>Lens &amp; Trail es un pequeño club para quienes viven en Edimburgo y sus alrededores y disfrutan de la fotografía y las caminatas, casi siempre a la vez.</p>"
        "<p>Nos reunimos dos veces al mes: una para hacer una excursión por las Pentland Hills, por la costa o más lejos, en las Highlands, y otra en un café del centro para ver las fotos de todos con una taza de té. De vez en cuando también salimos de noche a fotografiar las luces de la ciudad desde Calton Hill.</p>"
        "<p>Muchos de nuestros miembros llegaron a Escocia desde España y América Latina, así que en el camino se oye tanto español como inglés. Todo el mundo es bienvenido, tenga la cámara que tenga. ¡Un teléfono también sirve!</p>"
        "<p>El club tiene unos cuarenta miembros, y cada mes se suman nuevos.</p>"),
    "How to join": ("Cómo unirse", "/unete",
        "<p>Antes de nada, ven a una de nuestras excursiones o tardes de fotografía para ver si el club es para ti. No hace falta avisar.</p>"
        "<p>Si quieres hacerte miembro, habla con la secretaría ese mismo día o escribe a hello@lens-and-trail.ddev.site.</p>"
        "<p>La cuota es de 20 £ al año (10 £ para estudiantes). Cubre la sala de las tardes de fotografía y el seguro del club para las excursiones.</p>"),
    "Welcome to Lens & Trail": ("Te damos la bienvenida a Lens & Trail", "/bienvenida",
        "<p>Somos un club de fotografía y senderismo en Edimburgo. Caminamos, tomamos fotos y las compartimos.</p>"
        "<p>Lee más sobre el club o descubre cómo unirte.</p>"),
    "Privacy": ("Privacidad", "/privacidad",
        "<p>Lens &amp; Trail solo guarda lo que necesita para llevar el club: tu nombre y tu dirección de correo electrónico si te haces miembro, y las fotos que decides compartir. Nunca vendemos ni cedemos tus datos.</p>"),
}
ES18_HIKES = {
    "Turnhouse Hill and Carnethy Hill": ("Turnhouse Hill y Carnethy Hill", "Estacionamiento de Flotterstone",
        "<p>Dos de las cumbres más conocidas de las Pentland Hills, con vistas sobre Edimburgo y el estuario del Forth en un día despejado. Subimos a ritmo constante desde Flotterstone hasta Turnhouse Hill, seguimos la cresta hasta Carnethy Hill y bajamos por el valle.</p>"
        "<p>Trae botas, una chaqueta impermeable, algo de abrigo, comida, tu cámara y una linterna frontal: en noviembre oscurece antes de las cinco. El camino es empinado en algunos tramos y puede haber barro.</p>"),
    "Arthur's Seat at sunrise": ("Arthur's Seat al amanecer", "Estacionamiento del palacio de Holyrood",
        "<p>Madrugamos para tener la mejor luz del día: subimos a Arthur's Seat por el sendero de Salisbury Crags, a tiempo para ver salir el sol sobre el estuario del Forth. Trae una linterna frontal para la subida.</p>"),
    "North Berwick Law and the harbour": ("North Berwick Law y el puerto", "Estación de tren de North Berwick",
        "<p>Una subida corta a North Berwick Law, con el arco de hueso de ballena en la cima y vistas a Bass Rock; después bajamos al puerto a comer. Tomamos el tren desde Edinburgh Waverley a las 8:55.</p>"),
    "Glencorse Reservoir winter loop": ("Vuelta invernal al embalse de Glencorse", "Estacionamiento de Flotterstone",
        "<p>Un paseo tranquilo junto al embalse, con vuelta por las laderas bajas; ideal para la luz de invierno sobre el agua. Una buena primera excursión con el club.</p>"),
    "Pentland Hills ridge": ("La cresta de las Pentland Hills", "Estacionamiento de Flotterstone",
        "<p>La cresta entera, de Turnhouse Hill a Carnethy, Scald Law y los Kips, con vuelta por el valle. Un día largo y con mucho desnivel: trae comida y agua de sobra.</p>"),
}
ES18_LUCIA = ("Arthur's Seat by night", "Arthur's Seat de noche", "Holyrood Park, estacionamiento de St Margaret's Loch")
ES18_OTHER_NODES = {
    "The club has a website": ("El club tiene sitio web",
        "<p>Por fin Lens &amp; Trail tiene su propio sitio web. A partir de ahora encontrarás aquí el programa de excursiones, las noticias del club y las mejores fotos de los miembros.</p>"
        "<p>El sitio es nuevo y lo vamos construyendo sobre la marcha. Si falta algo o hay un error, díselo a la secretaría.</p>"),
    "Pentlands, 21 November": ("Pentlands, 21 de noviembre",
        "<p>Nuestra primera excursión con el nuevo sitio web: Turnhouse Hill y Carnethy Hill, con sol, viento y, cerca de la cima, un poco de nieve.</p>"),
    "Edinburgh, 24 October": ("Edimburgo, 24 de octubre",
        "<p>El amanecer desde Arthur's Seat y, de vuelta a casa, el casco antiguo desde Calton Hill.</p>"),
}
ES18_TERMS = {
    "Pentland Hills": ("Pentland Hills", "<p>Una cadena de colinas al suroeste de Edimburgo, casi toda parque regional. La favorita del club: un autobús desde el centro te deja al pie de las colinas.</p>"),
    "Turnhouse Hill": ("Turnhouse Hill", None), "Carnethy Hill": ("Carnethy Hill", None),
    "Glencorse Reservoir": ("Embalse de Glencorse", None),
    "Edinburgh": ("Edimburgo", "<p>Colinas, playas y miradores dentro de la ciudad: caminatas que puedes hacer en una tarde.</p>"),
    "Arthur's Seat": ("Arthur's Seat", None), "Calton Hill": ("Calton Hill", None), "Portobello": ("Portobello", None),
    "East Lothian": ("East Lothian", "<p>La costa y las colinas al este de Edimburgo.</p>"),
    "North Berwick Law": ("North Berwick Law", None),
    "Landscape": ("Paisaje", None), "Water": ("Agua", None), "Winter": ("Invierno", None), "City": ("Ciudad", None), "Hills": ("Colinas", None),
}
ES18_MEDIA = {
    "Turnhouse Hill across Glencorse Reservoir": ("Turnhouse Hill al otro lado del embalse de Glencorse", "Turnhouse Hill visto al otro lado del embalse de Glencorse, con una barca de remos en el embarcadero"),
    "Edinburgh's Old Town from Calton Hill": ("El casco antiguo de Edimburgo desde Calton Hill", "El casco antiguo de Edimburgo y el castillo vistos desde Calton Hill, con árboles delante"),
    "Carnethy Hill from Turnhouse Hill": ("Carnethy Hill desde Turnhouse Hill", "El sendero que baja de Turnhouse Hill, con Carnethy Hill alzándose detrás"),
    "The view from Carnethy Hill": ("La vista desde Carnethy Hill", "Colinas verdes y onduladas bajo un cielo nublado, vistas desde la cima pedregosa de Carnethy Hill"),
    "Glencorse Reservoir from the hillside": ("El embalse de Glencorse desde la ladera", "El embalse de Glencorse entre las colinas, visto desde una ladera de hierba con dos árboles"),
    "A burn in the Pentland Hills in winter": ("Un arroyo en las Pentland Hills en invierno", "Un arroyo que atraviesa un valle nevado en las Pentland Hills"),
}
ES18_BLOCKS = {
    "Club info": ("Información del club", {"field_meeting_times": {"value": "<p><strong>Excursiones:</strong> un sábado sí y otro no, a las 9:30.<br><strong>Tardes de fotografía:</strong> el primer jueves de cada mes a las 19:00, en un café de Leith.</p>", "format": "basic_html"}}),
    "Join the club": ("Únete al club", {"body": {"value": "<p>Siempre hay sitio para gente nueva, traigas cámara, botas o las dos cosas. La cuota es de 20 £ al año, 10 £ para estudiantes.</p><p><a href=\"/es/unete\">Cómo unirse</a></p>", "format": "basic_html"}}),
}
ES18_LINKS = {"About": "Nosotros", "Join us": "Únete", "Hike archive": "Archivo de excursiones", "Privacy": "Privacidad", "Upcoming hikes (RSS)": "Próximas excursiones (RSS)"}
ES18_PATTERNS = [
    ("hikes_es", "Excursiones", "canonical_entities:node", "/excursiones/[node:title]", ["hike"]),
    ("albums_es", "Álbumes", "canonical_entities:node", "/albumes/[node:title]", ["gallery"]),
    ("news_es", "Noticias", "canonical_entities:node", "/noticias/[node:title]", ["news"]),
    ("areas_es", "Zonas", "canonical_entities:taxonomy_term", "/zonas/[term:parents:join-path]/[term:name]", ["areas"]),
    ("photo_themes_es", "Temas fotográficos", "canonical_entities:taxonomy_term", "/temas-fotograficos/[term:name]", ["photo_themes"]),
]
# Configuration in Spanish: (config name, key, Spanish). The Hikes view's page is translated in the form.
ES18_CONFIG = [
    ("system.site", "slogan", "Fotos y excursiones por Edimburgo"),
    ("core.date_format.day_date_and_time", "pattern", "l, j \\d\\e F \\d\\e Y, \\a \\l\\a\\s H:i"),
    ("views.view.hikes", "display.block_1.display_options.title", "Próximas excursiones"),
    ("views.view.hikes", "display.block_1.display_options.use_more_text", "Todas las próximas excursiones"),
    ("views.view.hikes", "display.page_2.display_options.menu.title", "Excursiones"),
    ("views.view.hikes", "display.page_3.display_options.title", "Archivo de excursiones"),
    ("views.view.hikes", "display.default.display_options.empty.area.content.value", "<p>No hay excursiones previstas por ahora. Solemos anunciarlas con un mes de antelación, así que vuelve pronto.</p>"),
    ("views.view.albums", "display.default.display_options.title", "Álbumes"),
    ("views.view.albums", "display.block_1.display_options.title", "Álbumes de esta excursión"),
    ("views.view.albums", "display.page_1.display_options.menu.title", "Álbumes"),
    ("views.view.photos", "display.default.display_options.title", "Fotos más recientes"),
    ("block.block.olivero_join_the_club", "settings.label", "Únete al club"),
    ("field.field.node.hike.field_date", "label", "Fecha"),
    ("field.field.node.hike.field_meeting_place", "label", "Punto de encuentro"),
    ("field.field.node.hike.field_distance", "label", "Distancia"),
    ("field.field.node.hike.field_difficulty", "label", "Dificultad"),
    ("field.field.node.hike.field_hike_leader", "label", "Guía"),
    ("field.field.node.hike.field_area", "label", "Zona"),
    ("field.field.node.hike.field_body", "label", "Descripción"),
    ("field.field.node.gallery.field_area", "label", "Zona"),
    ("field.field.node.gallery.field_hike", "label", "Excursión"),
    ("field.field.node.gallery.field_body", "label", "Descripción"),
    ("field.field.node.gallery.comment", "label", "Comentarios"),
    ("field.field.media.image.field_photographer", "label", "Fotografía de"),
    ("field.field.media.image.field_license", "label", "Licencia"),
    ("field.field.media.image.field_source", "label", "Fuente"),
    ("field.field.block_content.club_info.field_meeting_times", "label", "Horarios"),
    ("field.field.block_content.club_info.field_email", "label", "Correo electrónico"),
    ("field.field.block_content.club_info.field_follow_us", "label", "Síguenos"),
    ("views.view.albums", "display.default.display_options.fields.title_1.label", "Excursión"),
    ("field.storage.node.field_difficulty", "settings.allowed_values", [{"value": "easy", "label": "Fácil"}, {"value": "moderate", "label": "Moderada"}, {"value": "hard", "label": "Difícil"}]),
]


def i18n18_restore(site: dict, page: Page) -> None:
    """Back to the end of Chapter 17 (a DDEV snapshot), and log in again: the sessions were in the database too."""
    subprocess.run(["ddev", "snapshot", "restore", "ch17-done"], cwd=site["dir"], check=True, capture_output=True)
    drush(site, "cache:rebuild")
    log_in(page, site)


def i18n18_php(site: dict, php: str, data) -> str:
    """Runs PHP with data from Python, passed as a JSON file in the project folder ($data in PHP)."""
    path = Path(site["dir"]) / "i18n18-data.json"
    path.write_text(json.dumps(data, ensure_ascii=False))
    try:
        return drush_php(site, "$data = json_decode(file_get_contents('/var/www/html/i18n18-data.json'), TRUE);\n" + php)
    finally:
        path.unlink()


def i18n18_translate_background(site: dict, skip: list[str]) -> None:
    """Translates the club's content into Spanish without the browser, except the titles in skip."""
    data = {
        "pages": {k: v for k, v in ES18_PAGES.items() if k not in skip},
        "hikes": {k: v for k, v in ES18_HIKES.items() if k not in skip},
        "nodes": {k: v for k, v in ES18_OTHER_NODES.items() if k not in skip},
        "terms": ES18_TERMS, "media": ES18_MEDIA, "blocks": ES18_BLOCKS, "links": ES18_LINKS,
    }
    i18n18_php(site, r"""
$etm = \Drupal::entityTypeManager();
$copy = function ($e) {
  $values = [];
  foreach ($e->getTranslatableFields(FALSE) as $name => $f) { $values[$name] = $f->getValue(); }
  foreach (['langcode', 'default_langcode', 'content_translation_source', 'content_translation_outdated', 'revision_translation_affected', 'content_translation_uid', 'content_translation_status', 'content_translation_created', 'content_translation_changed'] as $k) { unset($values[$k]); }
  return $values;
};
$tr = function ($e) use ($copy) {
  if ($e->hasTranslation('es')) { return $e->getTranslation('es'); }
  $t = $e->addTranslation('es', $copy($e));
  $t->set('content_translation_source', 'en');
  return $t;
};
$node = fn($title) => current($etm->getStorage('node')->loadByProperties(['title' => $title]));
$publish = function ($t) { if ($t->hasField('moderation_state')) { $t->set('moderation_state', 'published'); } else { $t->setPublished(); } $t->save(); };
foreach ($data['pages'] as $title => [$es, $alias, $body]) {
  $n = $node($title); $t = $tr($n);
  $t->set('title', $es); $t->set('field_body', ['value' => $body, 'format' => 'basic_html']); $t->set('path', ['alias' => $alias, 'pathauto' => 0]); $publish($t);
}
foreach ($data['hikes'] as $title => [$es, $place, $body]) {
  $n = $node($title); $t = $tr($n);
  $t->set('title', $es); $t->set('field_meeting_place', $place); $t->set('field_body', ['value' => $body, 'format' => 'basic_html']); $t->set('path', ['pathauto' => 1]); $publish($t);
}
foreach ($data['nodes'] as $title => [$es, $body]) {
  $n = $node($title); $t = $tr($n);
  $t->set('title', $es); $t->set('field_body', ['value' => $body, 'format' => 'basic_html']); $t->set('path', ['pathauto' => 1]); $publish($t);
}
foreach ($data['terms'] as $name => [$es, $desc]) {
  $term = current($etm->getStorage('taxonomy_term')->loadByProperties(['name' => $name]));
  $t = $tr($term); $t->setName($es); $t->set('path', ['pathauto' => 1]);
  if ($desc) { $t->setDescription($desc); $t->setFormat('basic_html'); }
  $t->save();
}
foreach ($data['media'] as $name => [$es, $alt]) {
  $m = current($etm->getStorage('media')->loadByProperties(['name' => $name]));
  $t = $tr($m); $t->setName($es); $t->get('field_media_image')->alt = $alt; $t->save();
}
foreach ($data['blocks'] as $info => [$es, $fields]) {
  $b = current($etm->getStorage('block_content')->loadByProperties(['info' => $info]));
  $t = $tr($b); $t->set('info', $es); foreach ($fields as $f => $v) { $t->set($f, $v); } $t->save();
}
foreach ($data['links'] as $title => $es) {
  $l = current($etm->getStorage('menu_link_content')->loadByProperties(['title' => $title]));
  $t = $tr($l); $t->set('title', $es); $t->save();
}
""", data)


def i18n18_patterns_background(site: dict) -> None:
    """The Spanish Pathauto patterns, except the first (made in the form), above the English ones."""
    i18n18_php(site, r"""
foreach ($data as [$id, $label, $type, $pattern, $bundles]) {
  $p = \Drupal\pathauto\Entity\PathautoPattern::load($id);
  if (!$p) {
    $p = \Drupal\pathauto\Entity\PathautoPattern::create(['id' => $id, 'label' => $label, 'type' => $type, 'pattern' => $pattern]);
    $entity = $type == 'canonical_entities:node' ? 'node' : 'taxonomy_term';
    $p->addSelectionCondition(['id' => 'entity_bundle:' . $entity, 'bundles' => array_combine($bundles, $bundles), 'negate' => FALSE, 'context_mapping' => [$entity => $entity]]);
    $p->addSelectionCondition(['id' => 'language', 'langcodes' => ['es' => 'es'], 'negate' => FALSE, 'context_mapping' => ['language' => $entity . ':langcode:language']]);
    $p->addRelationship($entity . ':langcode:language', 'Language');
  }
  $p->set('weight', -10); $p->save();
}
$p = \Drupal\pathauto\Entity\PathautoPattern::load('excursiones'); $p->set('weight', -10); $p->save();
""", ES18_PATTERNS[1:])


def i18n18_config_background(site: dict, skip: list[str] | None = None) -> None:
    i18n18_php(site, r"""
foreach ($data as [$name, $key, $value]) {
  \Drupal::languageManager()->getLanguageConfigOverride('es', $name)->set($key, $value)->save();
}
""", [c for c in ES18_CONFIG if not skip or c[0] not in skip])
    drush(site, "cache:rebuild")


def i18n18_setup_steps(page: Page, site: dict, snap) -> None:
    """Chapter 18 on core: languages, interface translation, detection, the switcher, content translation, Spanish aliases."""
    url = site["url"]
    i18n18_restore(site, page)
    # The four modules.
    page.goto(url + "/admin/modules")
    page.wait_for_load_state("networkidle")
    for m in ["language", "locale", "content_translation", "config_translation"]:
        page.check(f"input[name='modules[{m}][enable]']")
    scroll_to(page, "input[name='modules[config_translation][enable]']", offset=250)
    snap("18-extend")
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    # Spanish.
    page.goto(url + "/admin/config/regional/language/add")
    page.wait_for_load_state("networkidle")
    page.select_option("select[name='predefined_langcode']", "es")
    snap("18-add-language")
    page.click("input[name='add_language']")
    page.wait_for_url("**/admin/config/regional/language", timeout=300000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    snap("18-languages")
    views_admin_shot(page, url, "/admin/config/regional/language/detection", "18-detection", full=False)
    views_admin_shot(page, url, "/admin/config/regional/language/detection/url", "18-url-prefixes", full=False)
    # The language switcher in Olivero's Secondary menu region.
    page.goto(url + "/admin/structure/block/add/language_block%3Alanguage_interface/olivero?region=secondary_menu")
    page.wait_for_load_state("networkidle")
    page.uncheck("input[name='settings[label_display]']")
    snap("18-switcher-block")
    with page.expect_navigation():
        page.click("input[value='Save block']")
    page.wait_for_load_state("networkidle")
    as_visitor(page, site, "/es", "18-es-front-interface")
    # Which content can be translated.
    page.goto(url + "/admin/config/regional/content-language")
    page.wait_for_load_state("networkidle")
    for et in ["node", "taxonomy_term", "media", "block_content", "menu_link_content"]:
        page.check(f"input[name='entity_types[{et}]']")
    page.wait_for_timeout(500)
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    page.wait_for_timeout(500)
    for et, bundle, fields in [("node", "page", ["field_body"]), ("node", "hike", ["field_body", "field_meeting_place"]),
                               ("node", "news", ["field_body"]), ("node", "gallery", ["field_body"]),
                               ("taxonomy_term", "areas", []), ("taxonomy_term", "photo_themes", []), ("media", "image", []),
                               ("block_content", "basic", ["body"]), ("block_content", "club_info", ["field_meeting_times"]),
                               ("menu_link_content", "menu_link_content", [])]:
        page.check(f"input[name='settings[{et}][{bundle}][translatable]']")
        page.wait_for_timeout(200)
        # Checking the type checks all its fields: keep only the ones that hold words.
        for box in page.locator(f"input[name^='settings[{et}][{bundle}][fields][']").all():
            name = box.get_attribute("name")
            field = name.split("[fields][")[1].rstrip("]")
            if field.startswith("field_") or field in ("body", "comment"):
                box.set_checked(field in fields)
        if (et, bundle) == ("media", "image"):
            page.check("input[name='settings[media][image][fields][field_media_image]']")
            page.uncheck("input[name='settings[media][image][columns][field_media_image][file]']")
        hide = f"input[name='settings[{et}][{bundle}][settings][content_translation][untranslatable_fields_hide]']"
        if page.locator(hide).count():
            page.check(hide)
    scroll_to(page, "input[name='settings[node][hike][fields][field_area]']", offset=350)
    snap("18-content-language")
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    # A Spanish pattern for hikes; the others in the background.
    add_pattern(page, url, "canonical_entities:node", "/excursiones/[node:title]", ["hike"], "Excursiones",
                lambda: (page.check("input[name='languages[es]']"), page.wait_for_timeout(300), snap("18-pattern-es")))
    i18n18_patterns_background(site)
    page.goto(url + "/admin/config/search/path/patterns")
    page.wait_for_load_state("networkidle")
    page.set_viewport_size({"width": WIDTH, "height": page.evaluate("document.documentElement.scrollHeight")})
    page.wait_for_timeout(800)
    snap("18-patterns")
    page.set_viewport_size({"width": WIDTH, "height": 1000})
    # About the club, translated in the form.
    page.goto(url + "/node/1/translations")
    page.wait_for_load_state("networkidle")
    snap("18-translations-about")
    page.goto(url + "/es/node/1/translations/add/en/es")
    page.wait_for_load_state("networkidle")
    title, alias, body = ES18_PAGES["About the club"]
    page.fill("input[name='title[0][value]']", title)
    page.evaluate("h => document.querySelector('.ck-editor__editable').ckeditorInstance.setData(h)", body)
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    page.fill("input[name='path[0][alias]']", alias)
    page.select_option("select[name='moderation_state[0][state]']", "published")
    page.wait_for_timeout(500)
    snap("18-translate-about")
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    # The Turnhouse hike: the shared fields are hidden, and the alias is typed by hand.
    nid = drush_php(site, "echo current(\\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => 'Turnhouse Hill and Carnethy Hill']))->id();").strip()
    page.goto(url + f"/es/node/{nid}/translations/add/en/es")
    page.wait_for_load_state("networkidle")
    title, place, body = ES18_HIKES["Turnhouse Hill and Carnethy Hill"]
    page.fill("input[name='title[0][value]']", title)
    page.fill("input[name='field_meeting_place[0][value]']", place)
    page.evaluate("h => document.querySelector('.ck-editor__editable').ckeditorInstance.setData(h)", body)
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    page.fill("input[name='path[0][alias]']", "/excursiones/turnhouse-hill")
    page.select_option("select[name='moderation_state[0][state]']", "published")
    page.wait_for_timeout(500)
    page.evaluate("() => window.scrollTo(0, 0)")
    snap("18-translate-hike")
    with page.expect_navigation():
        page.click("#edit-submit")
    page.wait_for_load_state("networkidle")
    # Everything else, in the background.
    i18n18_translate_background(site, ["About the club", "Turnhouse Hill and Carnethy Hill"])
    drush(site, "cache:rebuild")
    page.goto(url + "/admin/config/search/path?search=")
    page.wait_for_load_state("networkidle")
    page.set_viewport_size({"width": WIDTH, "height": page.evaluate("document.documentElement.scrollHeight")})
    page.wait_for_timeout(800)
    snap("18-aliases")
    page.set_viewport_size({"width": WIDTH, "height": 1000})
    views_admin_shot(page, url, "/admin/content", "18-content", full=False)


ES18_VIEWS = {"hikes": ("node_field_data", "node", []), "albums": ("node_field_data", "node", ["field_hike"]),
              "hike_admin": ("node_field_data", "node", []), "photos": ("media_field_data", "media", []),
              "photo_credits": ("media_field_data", "media", ["reverse__node__field_photos"]), "photographers": ("media_field_data", "media", [])}


def i18n18_views_background(site: dict) -> None:
    """One row per item on the club's views: a Default translation filter on every display with filters (and on the
    relationships), and the page's language as the rendering language, so a missing translation falls back to English."""
    i18n18_php(site, r"""
foreach ($data as $id => [$table, $entity, $relationships]) {
  $view = \Drupal::configFactory()->getEditable('views.view.' . $id);
  foreach ($view->get('display') as $d => $display) {
    // Rendering language is set per display: displays don't inherit it from the default display.
    $view->set("display.$d.display_options.rendering_language", '***LANGUAGE_language_interface***');
    if (!isset($display['display_options']['filters'])) { continue; }
    foreach (array_merge(['none'], $relationships) as $i => $rel) {
      $key = $i ? 'default_langcode_' . $i : 'default_langcode';
      if (isset($display['display_options']['filters'][$key])) { continue; }
      $view->set("display.$d.display_options.filters.$key", [
        'id' => $key, 'table' => $rel == 'none' ? $table : 'node_field_data', 'field' => 'default_langcode', 'relationship' => $rel,
        'group_type' => 'group', 'admin_label' => '', 'entity_type' => $rel == 'none' ? $entity : 'node', 'entity_field' => 'default_langcode',
        'plugin_id' => 'boolean', 'operator' => '=', 'value' => '1',
        'group' => 1, 'exposed' => FALSE, 'is_grouped' => FALSE,
        'expose' => ['operator_id' => '', 'label' => '', 'description' => '', 'use_operator' => FALSE, 'operator' => '', 'operator_limit_selection' => FALSE, 'operator_list' => [], 'identifier' => '', 'required' => FALSE, 'remember' => FALSE, 'multiple' => FALSE, 'remember_roles' => ['authenticated' => 'authenticated']],
        'group_info' => ['label' => '', 'description' => '', 'identifier' => '', 'optional' => TRUE, 'widget' => 'select', 'multiple' => FALSE, 'remember' => FALSE, 'default_group' => 'All', 'default_group_multiple' => [], 'group_items' => []],
      ]);
    }
  }
  $view->save();
}
""", ES18_VIEWS)
    drush(site, "cache:rebuild")


def i18n18_views_steps(page: Page, site: dict, snap) -> None:
    """Chapter 18 on core: why every hike shows twice, the Default translation filter and the rendering language (after i18n18_setup_steps)."""
    url = site["url"]
    # View pages have no Pathauto pattern: their Spanish aliases are added by hand.
    drush_php(site, """
$storage = \\Drupal::entityTypeManager()->getStorage('path_alias');
foreach (['/hikes' => '/excursiones', '/hikes/archive' => '/excursiones/archivo', '/galleries' => '/albumes'] as $path => $alias) {
  if (!$storage->loadByProperties(['path' => $path, 'langcode' => 'es'])) {
    $storage->create(['path' => $path, 'alias' => $alias, 'langcode' => 'es'])->save();
  }
}
""")
    as_visitor(page, site, "/es/excursiones", "18-es-hikes-twice")
    page.goto(url + "/admin/structure/views/view/hikes/edit/block_1")
    page.wait_for_load_state("networkidle")
    views_add(page, "hikes/block_1/filter", "Default translation", "node_field_data.default_langcode")
    page.check(".ui-dialog input[name='options[value]'][value='1']")
    page.wait_for_timeout(300)
    snap("18-views-default-translation", element=".ui-dialog")
    views_apply(page)
    views_dialog(page, "display/hikes/block_1/rendering_language")
    page.select_option(".ui-dialog select[name='rendering_language']", "***LANGUAGE_language_interface***")
    page.wait_for_timeout(300)
    snap("18-views-rendering-language", element=".ui-dialog")
    views_apply(page)
    views_save(page)
    i18n18_views_background(site)
    as_visitor(page, site, "/es/excursiones", "18-es-hikes")


def i18n18_config_steps(page: Page, site: dict, snap) -> None:
    """Chapter 18 on core: configuration and interface translation, and the club in Spanish (after i18n18_setup_steps)."""
    url = site["url"]
    views_admin_shot(page, url, "/admin/config/regional/config-translation", "18-config-translation", full=False)
    # The Hikes view, in the form.
    page.goto(url + "/admin/structure/views/view/hikes/translate/es/add")
    page.wait_for_load_state("networkidle")
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    t = "translation[config_names][views.view.hikes][display]"
    page.fill(f"textarea[name='{t}[default][display_options][title]']", "Próximas excursiones")
    page.fill(f"textarea[name='{t}[page_1][display_options][menu][title]']", "Excursiones")
    scroll_to(page, f"textarea[name='{t}[default][display_options][title]']", offset=250)
    snap("18-translate-view")
    with page.expect_navigation():
        page.click("input[value='Save translation']")
    page.wait_for_load_state("networkidle")
    i18n18_config_background(site)
    # Interface text: Drupal's own strings, from localize.drupal.org.
    page.goto(url + "/admin/config/regional/translate?string=Log+in&langcode=es&translation=all")
    page.wait_for_load_state("networkidle")
    snap("18-interface-translation")
    # The club in Spanish.
    # 1440 wide: at 1280 the longer Spanish menu labels make Olivero switch to its mobile menu.
    as_visitor(page, site, "/es", "18-es-front", width=1440)
    as_visitor(page, site, "/es/excursiones/turnhouse-hill", "18-es-hike", width=1440)
    as_visitor(page, site, "/es/unete", "18-es-join", width=1440)


def i18n18_people_steps(page: Page, site: dict, snap) -> None:
    """Chapter 18 on core: a Translator role for Lucía, who translates and publishes a hike (after i18n18_config_steps).

    Lucía publishes herself: on Drupal 12.0.0-beta2 the Default Admin theme hides the moderation select from users who
    can translate but not edit (see PROJECT-LOG backlog), so a Spanish draft for Morag to publish isn't possible yet.
    """
    url = site["url"]
    subprocess.run(["ddev", "drush", "role:delete", "translator"], cwd=site["dir"], capture_output=True)
    drush(site, "role:create", "translator", "Translator")
    drush(site, "role:perm:add", "translator", ",".join([
        "create content translations", "update content translations", "translate hike node", "translate page node",
        "translate news node", "translate gallery node", "use editorial transition publish", "view latest version",
        "view the administration theme", "access navigation"]))
    drush(site, "user:role:add", "translator", "lucia")
    page.goto(url + "/admin/people/permissions/translator")
    page.wait_for_load_state("networkidle")
    scroll_to(page, "input[name='translator[create content translations]']", offset=250)
    snap("18-translator-permissions")
    nid = drush_php(site, f"echo current(\\Drupal::entityTypeManager()->getStorage('node')->loadByProperties(['title' => {php_str(ES18_LUCIA[0])}]))->id();").strip()
    context, lucia = as_user(page, site, "lucia")
    lucia.goto(url + f"/es/node/{nid}/translations/add/en/es")
    lucia.wait_for_load_state("networkidle")
    lucia.fill("input[name='title[0][value]']", ES18_LUCIA[1])
    lucia.fill("input[name='field_meeting_place[0][value]']", ES18_LUCIA[2])
    lucia.wait_for_timeout(300)
    save(lucia, "18-lucia-translate")
    with lucia.expect_navigation():
        lucia.click("#edit-submit")
    lucia.wait_for_load_state("networkidle")
    context.close()
    page.goto(url + f"/node/{nid}/translations")
    page.wait_for_load_state("networkidle")
    snap("18-translations-lucia")


CMS18_JOIN = {
    "title": "Cómo unirse",
    "card": "Cuándo y dónde",
    "text": "<p>Antes de nada, ven a una de nuestras excursiones o tardes de fotografía para ver si el club es para ti. No hace falta avisar.</p>"
            "<p>Si quieres hacerte miembro, habla con la secretaría ese mismo día o escribe a hello@lens-and-trail-cms.ddev.site.</p>"
            "<p>La cuota es de 20 £ al año (10 £ para estudiantes). Cubre la sala de las tardes de fotografía y el seguro del club para las excursiones.</p>",
    "card_text": "<p>Excursiones: un sábado sí y otro no, a las 9:30. Una semana antes enviamos el punto de encuentro a quienes vienen.</p>"
                 "<p>Tardes de fotografía: el primer jueves de cada mes a las 19:00, en la sala del fondo de un café de Leith.</p>",
}


def i18n18_cms_steps(page: Page, site: dict, snap) -> None:
    """Chapter 18 on Drupal CMS: Spanish, Canvas pages made translatable, and How to join translated in Canvas Translate."""
    url = site["url"]
    i18n18_restore(site, page)
    drush(site, "pm:enable", "-y", "language", "locale", "content_translation", "config_translation", "canvas_translate")
    drush(site, "language:add", "es")
    drush(site, "cache:rebuild")
    # Canvas pages, and their fields, translatable.
    page.goto(url + "/admin/config/regional/content-language")
    page.wait_for_load_state("networkidle")
    page.check("input[name='entity_types[canvas_page]']")
    page.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
    page.check("input[name='settings[canvas_page][canvas_page][translatable]']")
    page.wait_for_timeout(500)
    for field in ["title", "description", "components", "path", "image"]:
        page.locator(f"input[name='settings[canvas_page][canvas_page][fields][{field}]']").set_checked(True)
    scroll_to(page, "input[name='settings[canvas_page][canvas_page][translatable]']", offset=200)
    snap("18-cms-content-language")
    with page.expect_navigation():
        page.locator("input[value='Save configuration']").last.evaluate("e => e.click()")
    page.wait_for_load_state("networkidle")
    # Work around the Canvas bug (PROJECT-LOG backlog): the Basic page template's empty heading link.
    script = Path(site["dir"]) / "remove-empty-heading-links.php"
    shutil.copy(ROOT / "examples/canvas-translate/remove-empty-heading-links.php", script)
    try:
        drush(site, "php:script", "remove-empty-heading-links.php")
    finally:
        script.unlink()
    drush(site, "cache:rebuild")
    # The dashboard.
    page.goto(url + "/canvas/app/canvas_translate")
    page.wait_for_load_state("networkidle")
    frame = page.frame_locator("iframe").first
    frame.locator("[title^='Translate “How to join”']").wait_for()
    page.wait_for_timeout(1500)
    snap("18-cms-translate-dashboard")
    # The editor: source on the left, Spanish on the right.
    frame.locator("[title^='Translate “How to join”']").click()
    targets = frame.locator("textarea[placeholder^='Add translation']")
    targets.first.wait_for()
    page.wait_for_timeout(1500)
    # The plain-text targets, in order: page title, meta description, heading, icon name, card heading.
    targets.nth(0).fill(CMS18_JOIN["title"])
    targets.nth(2).fill(CMS18_JOIN["title"])
    editors = frame.locator(".ck-editor__editable")
    editors.nth(0).evaluate("(e, html) => e.ckeditorInstance.setData(html)", CMS18_JOIN["text"])
    page.wait_for_timeout(500)
    targets.nth(4).fill(CMS18_JOIN["card"])
    editors.nth(1).evaluate("(e, html) => e.ckeditorInstance.setData(html)", CMS18_JOIN["card_text"])
    page.wait_for_timeout(3000)
    snap("18-cms-translate-editor")
    # Review and publish.
    frame.get_by_text("Review & publish").click()
    page.wait_for_timeout(2500)
    frame.locator("tr:has-text('How to join') button[role='checkbox'], tr:has-text('How to join') input[type='checkbox']").first.click()
    page.wait_for_timeout(500)
    snap("18-cms-translate-review")
    frame.get_by_text("Publish selected").click()
    page.wait_for_timeout(4000)
    as_visitor(page, site, "/es/join", "18-cms-es-join", width=1440)


# Chapter 19: the prompts, as the chapter prints them. The answers differ from run to run.
AI19_TAGS = "Our site is for Lens & Trail, a small photography and hiking club in Edinburgh. Please add 25 common tags to the Tags vocabulary that we can use for news, pages and photos."
AI19_FIELD = "Please add a Tags field to the Image media type, so we can tag photos with terms from the Tags vocabulary. A photo can have several tags."
AI19_PAGE = "Create a landing page called First hike with Lens & Trail, for people who have never been on a hike with the club: what to bring, what to expect on the day, and how to join."
AI19_FACTS = ("Create a landing page called First hike with Lens & Trail, for people who have never been on a hike with the club. "
              "Use only these facts and do not invent any others: hikes are every other Saturday at 9:30; "
              "we email the meeting point a week before to the people who are coming; you don't need to book, just come along; "
              "bring boots, a waterproof jacket, a warm layer, food, your camera and a head torch; the path can be steep and muddy; "
              "to become a member, talk to the club secretary on the day or email hello@lens-and-trail-cms.ddev.site; "
              "membership is £20 a year (£10 for students). No testimonials, no prices other than these, and no images.")


def ai19_chat_text(page: Page) -> str:
    """The conversation in the AI chat (a deep-chat web component, in its own shadow DOM)."""
    return page.evaluate("() => { const c = document.querySelector('deep-chat'); const m = c && c.shadowRoot && c.shadowRoot.querySelector('#messages'); return m ? m.innerText : ''; }")


def ai19_ask(page: Page, prompt: str, at_least: int = 30, quiet: int = 20, shot=None, done=None) -> str:
    """Types a prompt into the AI chat, sends it, and waits until the answer has stopped growing for `quiet` seconds."""
    before = len(ai19_chat_text(page))
    # Away from the navigation sidebar, which opens under the mouse and covers the chat.
    page.mouse.move(900, 500)
    page.locator("deep-chat #text-input").evaluate("e => e.focus()")
    page.keyboard.type(prompt)
    page.wait_for_timeout(500)
    if shot:
        shot()
    page.keyboard.press("Enter")
    waited, still, last = 0, 0, ""
    while waited < 900:
        page.wait_for_timeout(5000)
        waited += 5
        text = ai19_chat_text(page)
        still = still + 5 if text == last else 0
        last = text
        # The assistant shows "Contacting agents..." while its agents work. Canvas AI shows "Thinking", but
        # with Claude that stays on screen after the answer, so Canvas pages pass their own `done` instead.
        if done:
            finished = done(page)
        else:
            thinking = page.get_by_text("Thinking", exact=True)
            finished = not any(thinking.nth(i).is_visible() for i in range(thinking.count()))
        busy = "Contacting agents" in text or not finished
        if waited >= at_least and len(text) > before + 100 and still >= quiet and not busy:
            # Show the newest question and answer from their start.
            page.evaluate("() => { const m = document.querySelector('deep-chat').shadowRoot.querySelector('#messages'); const users = m.querySelectorAll('.user-message'); if (users.length) users[users.length - 1].scrollIntoView(); }")
            page.mouse.move(1100, 700)
            page.wait_for_timeout(1000)
            return text
    raise RuntimeError("The AI didn't answer within fifteen minutes")


def ai19_klaro_yes(page: Page, within: str = "body") -> None:
    """Klaro's consent question: Yes (this time). Clicked with JavaScript: the toolbar can cover it.

    `within` limits it to one part of the page: on a form, the chat's own question would open the chat too.
    """
    yes = page.locator(within).locator("text=Yes (this time)")
    for i in range(yes.count()):
        if yes.nth(i).is_visible():
            yes.nth(i).evaluate("e => e.click()")
            page.wait_for_timeout(2000)


def ai19_tidy(page: Page) -> None:
    """Closes the AI chat (it stays open from page to page) and moves the mouse off the navigation sidebar."""
    close = page.locator("button[data-action='close-chat']")
    for _ in range(3):
        # The button toggles: clicked while the chat is closed, it opens it. The body class says which it is.
        if not (close.count() and page.evaluate("() => document.body.classList.contains('ai-chatbot-opened')")):
            break
        close.first.evaluate("e => e.click()")
        page.wait_for_timeout(1000)
    page.mouse.move(1100, 700)
    page.wait_for_timeout(1000)


def ai19_canvas_page(page: Page, site: dict, prompt: str, shot_prompt=None) -> None:
    """A new Canvas page, built by Canvas AI from the prompt."""
    page.goto(site["url"] + "/admin/content/pages")
    page.wait_for_load_state("networkidle")
    page.click("a:has-text('Add Page')")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(6000)
    page.get_by_label("Open AI Panel").click()
    page.wait_for_timeout(2500)
    # Done when Canvas AI has put its changes on the page: the Review button counts them.
    ai19_ask(page, prompt, at_least=180, quiet=45, shot=(lambda: shot_prompt()) if shot_prompt else None,
             done=lambda p: p.locator("button:has-text('Review')").filter(has_text="change").count() > 0)
    page.wait_for_timeout(3000)


def ai19_cms_steps(page: Page, site: dict, snap) -> None:
    """Chapter 19 on Drupal CMS: the AI Assistant, the chatbot, alt text, Canvas AI and Canvas Translate AI.

    Starts from the end of Chapter 18 (a DDEV snapshot). Installs with amazee.ai, as the chapter does, then
    switches to Anthropic for the AI steps (needs the author's key), so it needs the internet, costs a little,
    and the AI's answers (and so the screenshots) are different every time.
    """
    url = site["url"]
    subprocess.run(["ddev", "snapshot", "restore", "ch18-done"], cwd=site["dir"], check=True, capture_output=True)
    drush(site, "cache:rebuild")
    log_in(page, site)

    # Installing the AI Assistant from Recommended add-ons.
    page.goto(url + "/admin/modules/browse/recommended")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(4000)
    card = page.locator("li", has_text="Adds integration with AI services").first
    card.scroll_into_view_if_needed()
    page.evaluate("window.scrollBy(0, 150)")
    page.wait_for_timeout(500)
    snap("19-cms-recommended")
    card.locator("button:text-is('Install')").first.click()
    page.locator(".ui-dialog-buttonpane button:has-text('Continue')").first.wait_for(timeout=60000)
    page.wait_for_timeout(1000)
    snap("19-cms-provider", element=".ui-dialog")
    page.locator(".ui-dialog-buttonpane button:has-text('Continue')").first.click()
    for _ in range(80):
        page.wait_for_timeout(5000)
        if "Installed" in card.inner_text() or page.locator(".ui-dialog:has-text('Error')").count():
            break
    if "Installed" not in card.inner_text():
        raise RuntimeError("Project Browser didn't install the AI Assistant")
    drush(site, "cache:rebuild")
    page.goto(url + "/admin/config/ai")
    page.wait_for_load_state("networkidle")
    # The dashboard's Filter box takes the focus, and scrolls the page down to it.
    page.wait_for_timeout(1500)
    page.evaluate("() => { document.activeElement && document.activeElement.blur(); window.scrollTo(0, 0); }")
    ai19_tidy(page)
    snap("19-cms-ai-dashboard")
    # The figures from here on are taken with Anthropic: amazee.ai's trial without an account runs out after
    # a few runs (the chapter says so). Needs the key, see ai19_anthropic_key().
    ai19_use_anthropic(page, site)

    # The chatbot: tags, then a field.
    tags = url + "/admin/structure/taxonomy/manage/tags/overview"
    page.goto(tags)
    page.wait_for_load_state("networkidle")
    page.locator("button.button--ai-chatbot").evaluate("e => e.click()")
    page.wait_for_timeout(2000)
    snap("19-cms-chatbot-consent")
    ai19_klaro_yes(page)
    ai19_ask(page, AI19_TAGS)
    snap("19-cms-chatbot-tags")
    page.goto(tags)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    ai19_tidy(page)
    snap("19-cms-tags")
    page.locator("button.button--ai-chatbot").evaluate("e => e.click()")
    page.wait_for_timeout(2000)
    ai19_klaro_yes(page)
    ai19_ask(page, AI19_FIELD)
    snap("19-cms-chatbot-field")
    page.goto(url + "/admin/structure/media/manage/image/fields")
    page.wait_for_load_state("networkidle")
    ai19_tidy(page)
    snap("19-cms-media-fields")

    # Alt text.
    page.goto(url + "/admin/config/ai/ai_image_alt_text")
    page.wait_for_load_state("networkidle")
    ai19_tidy(page)
    snap("19-cms-alt-settings")
    page.goto(url + "/media/add/image")
    page.wait_for_load_state("networkidle")
    page.set_input_files("input[type='file']", str(PHOTOS / "portobello-beach.jpg"))
    page.wait_for_timeout(5000)
    ai19_tidy(page)
    snap("19-cms-alt-consent")
    ai19_klaro_yes(page, "form:has(input[name*='[alt]'])")
    page.locator("input[value='Generate with AI']").first.evaluate("e => e.click()")
    alt = page.locator("input[name*='[alt]']").first
    for _ in range(24):
        page.wait_for_timeout(2500)
        if alt.input_value():
            break
    page.wait_for_timeout(1000)
    scroll_to(page, "input[name*='[alt]']", offset=300)
    ai19_tidy(page)
    snap("19-cms-alt-generated")

    # Canvas AI: a short prompt, then one with the club's facts.
    ai19_canvas_page(page, site, AI19_PAGE, shot_prompt=lambda: snap("19-cms-canvas-ai-prompt"))
    snap("19-cms-canvas-ai-page")
    ai19_canvas_page(page, site, AI19_FACTS)
    snap("19-cms-canvas-ai-facts")
    # The review: the title and URL alias in Page data, then publish only this page.
    page.get_by_text("Page data", exact=True).first.click()
    page.wait_for_timeout(1000)
    page.locator("#edit-title-0-value").fill("First hike with Lens & Trail")
    page.locator("#edit-path-0-alias").fill("/first-hike")
    page.wait_for_timeout(3000)
    page.locator("button:has-text('Review')").filter(has_text="change").first.click()
    page.wait_for_timeout(2000)
    page.get_by_label("Select change First hike with Lens & Trail").click()
    page.wait_for_timeout(1000)
    snap("19-cms-review-changes")
    page.locator("button:has-text('Publish 1 selected')").click()
    page.wait_for_timeout(6000)
    # What the reader corrects by hand in the components: the "&amp;" Canvas AI writes for "&" (see the chapter).
    drush_php(site, r"""
$pages = \Drupal::entityTypeManager()->getStorage('canvas_page')->loadByProperties(['title' => 'First hike with Lens & Trail']);
$p = reset($pages);
$items = $p->get('components')->getValue();
foreach ($items as &$item) {
  // The inputs are JSON, where "&" is stored as \u0026: decode them, fix the values, encode them again.
  $inputs = is_string($item['inputs']) ? json_decode($item['inputs'], TRUE) : $item['inputs'];
  array_walk_recursive($inputs, function (&$value) { if (is_string($value)) { $value = str_replace('&amp;', '&', $value); } });
  $item['inputs'] = is_string($item['inputs']) ? json_encode($inputs) : $inputs;
}
$p->set('components', $items);
$p->set('description', str_replace('&amp;', '&', (string) $p->get('description')->value));
$p->save();
""")

    # Canvas Translate AI.
    drush(site, "pm:enable", "-y", "canvas_translate_ai")
    drush(site, "cache:rebuild")
    page.goto(url + "/canvas/app/canvas_translate")
    page.wait_for_load_state("networkidle")
    frame = page.frame_locator("iframe").first
    item = frame.locator("[title^='Translate “First hike with Lens & Trail”']")
    item.wait_for(timeout=60000)
    item.click()
    targets = frame.locator("textarea[placeholder^='Add translation']")
    targets.first.wait_for()
    page.wait_for_timeout(1500)
    frame.get_by_text("AI translate empty").click()
    for _ in range(60):
        page.wait_for_timeout(5000)
        if frame.locator("textarea[placeholder^='Add translation']").count() == 0 or "100%" in frame.locator("body").inner_text():
            break
    page.wait_for_timeout(2000)
    snap("19-cms-translate-ai")


def ai19_anthropic_key() -> str:
    """The Anthropic API key for the comparison: $ANTHROPIC_API_KEY, or the file ~/.config/lens-and-trail/anthropic-api-key.

    Kept out of the repository. Never printed.
    """
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    path = Path.home() / ".config" / "lens-and-trail" / "anthropic-api-key"
    if not key and path.exists():
        key = path.read_text().strip()
    return key


def ai19_use_anthropic(page: Page, site: dict, snap=None) -> None:
    """Connects Anthropic the way the chapter does: a key, the provider, and AI Settings.

    The key comes from ai19_anthropic_key(). With `snap`, takes the provider page and AI Settings
    (figures 19.17 and 19.18); without a key, takes only the provider page and returns.
    """
    url = site["url"]
    key = ai19_anthropic_key()
    if key:
        page.goto(url + "/admin/config/system/keys/add")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        page.fill("#edit-label", "Anthropic API key")
        # Wait for the machine name, which Drupal makes from the label.
        for _ in range(20):
            page.wait_for_timeout(500)
            if page.input_value("#edit-id"):
                break
        page.fill("#edit-key-input-settings-key-value", key)
        page.locator("#edit-submit").first.evaluate("e => e.click()")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        if "has been added" not in page.locator("body").inner_text():
            raise RuntimeError("The Anthropic key wasn't saved")
    page.goto(url + "/admin/config/ai/providers/anthropic")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)
    ai19_tidy(page)
    if key:
        page.select_option("select[name='api_key']", label="Anthropic API key")
        page.wait_for_timeout(1000)
    if snap:
        snap("19-cms-anthropic")
    if not key:
        if snap:
            print("No Anthropic API key: skipping the rest of the Anthropic sequence.")
            return
        raise RuntimeError("No Anthropic API key: see ai19_anthropic_key()")
    page.locator("#edit-submit").first.evaluate("e => e.click()")
    page.wait_for_load_state("networkidle")

    # AI Settings: Anthropic, Claude Sonnet 5.5, for the chat jobs, and no default for Translate Text, so
    # Canvas Translate AI falls back to chat. Set with Drush (the page's selects load their models by AJAX,
    # which is unreliable from a script), then shown on the page.
    drush_php(site, r"""
$config = \Drupal::configFactory()->getEditable('ai.settings');
$defaults = $config->get('default_providers');
// Not Chat with Complex JSON: ai_provider_anthropic 1.2.2 lists no Claude 5 models there (fixed in 1.3), so the chapter leaves it on amazee.ai.
foreach (['chat', 'chat_with_image_vision', 'chat_with_structured_response', 'chat_with_tools'] as $op) {
  $defaults[$op] = ['provider_id' => 'anthropic', 'model_id' => 'claude-sonnet-5-5'];
}
unset($defaults['translate_text']);
$config->set('default_providers', $defaults)->save();
""")
    if snap:
        page.goto(url + "/admin/config/ai/settings")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
        ai19_tidy(page)
        snap("19-cms-ai-settings")


def ai19_anthropic_steps(page: Page, site: dict, snap) -> None:
    """Chapter 19, the second provider: Anthropic's key and settings, then the same questions as with amazee.ai.

    Starts right after the AI Assistant was installed (a DDEV snapshot). Without a key (see ai19_anthropic_key),
    it only takes the provider page, with no key selected.
    """
    url = site["url"]
    subprocess.run(["ddev", "snapshot", "restore", "ch19-ai-installed"], cwd=site["dir"], check=True, capture_output=True)
    drush(site, "cache:rebuild")
    log_in(page, site)
    ai19_use_anthropic(page, site, snap)
    if not ai19_anthropic_key():
        return

    # The same questions as with amazee.ai: tags, alt text, and the short Canvas AI prompt.
    tags = url + "/admin/structure/taxonomy/manage/tags/overview"
    page.goto(tags)
    page.wait_for_load_state("networkidle")
    page.locator("button.button--ai-chatbot").evaluate("e => e.click()")
    page.wait_for_timeout(2000)
    ai19_klaro_yes(page)
    print("--- Tags\n" + ai19_ask(page, AI19_TAGS)[-4000:])
    snap("19-cms-anthropic-chatbot-tags")
    page.goto(tags)
    page.wait_for_load_state("networkidle")
    ai19_tidy(page)
    print("--- Terms\n" + page.locator("table").first.inner_text())
    page.goto(url + "/media/add/image")
    page.wait_for_load_state("networkidle")
    page.set_input_files("input[type='file']", str(PHOTOS / "portobello-beach.jpg"))
    page.wait_for_timeout(5000)
    ai19_tidy(page)
    ai19_klaro_yes(page, "form:has(input[name*='[alt]'])")
    page.locator("input[value='Generate with AI']").first.evaluate("e => e.click()")
    alt = page.locator("input[name*='[alt]']").first
    for _ in range(24):
        page.wait_for_timeout(2500)
        if alt.input_value():
            break
    print("--- Alt text\n" + alt.input_value())
    ai19_tidy(page)
    ai19_canvas_page(page, site, AI19_PAGE)
    print("--- Canvas AI\n" + ai19_chat_text(page)[-4000:])
    snap("19-cms-anthropic-page")


def safe20_restore(site: dict) -> None:
    """Back to the start of Chapter 20: the ch20-start snapshot, and the Composer files saved with it."""
    d = Path(site["dir"])
    subprocess.run(["ddev", "snapshot", "restore", "ch20-start"], cwd=d, check=True, capture_output=True)
    for f in ["composer.json", "composer.lock"]:
        shutil.copy(d / ".ddev" / f"ch20-start.{f}", d / f)
    subprocess.run(["ddev", "composer", "install"], cwd=d, check=True, capture_output=True)
    drush(site, "cache:rebuild")


def safe20_check(page: Page, url: str) -> None:
    """Available updates, after asking drupal.org again (Check manually)."""
    page.goto(url + "/admin/reports/updates", timeout=300000)
    page.wait_for_load_state("networkidle")
    page.locator("a:has-text('Check manually')").first.click()
    page.wait_for_url("**/admin/reports/updates", timeout=300000)
    page.wait_for_load_state("networkidle")


def safe20_composer(site: dict, *args: str) -> str:
    """Runs Composer and returns what it printed, for the text: blocked updates, audit."""
    result = subprocess.run(["ddev", "composer", *args], cwd=site["dir"], capture_output=True, text=True)
    return result.stdout + result.stderr


def safe20_core_steps(page: Page, site: dict, snap) -> None:
    """Chapter 20 on core: Available updates, its settings, a module update, the update emergency, maintenance mode."""
    url = site["url"]
    safe20_restore(site)
    log_in(page, site)
    safe20_check(page, url)
    page.get_by_label("Update available").first.check()
    page.wait_for_timeout(800)
    page.locator("body").click(position={"x": 5, "y": 5})
    snap("20-core-available-updates")
    page.goto(url + "/admin/reports/updates/settings")
    page.wait_for_load_state("networkidle")
    page.fill("textarea[name='update_notify_emails']", "webmaster@lensandtrail.example\nmorag@lensandtrail.example")
    page.check("input[name='update_notification_threshold'][value='security']")
    snap("20-core-update-settings")

    # Update Project Browser.
    print(safe20_composer(site, "outdated", "drupal/*"))
    composer(site, "update", "drupal/project_browser", "--with-all-dependencies")
    print(drush(site, "updatedb", "-y"))
    drush(site, "cache:rebuild")
    safe20_check(page, url)
    snap("20-core-up-to-date")
    print(safe20_composer(site, "audit"))

    # The update emergency: back to 12.0.0-beta1, which Composer refuses without --no-blocking.
    d = Path(site["dir"])
    keep = (d / "composer.json").read_text(), (d / "composer.lock").read_text()
    try:
        (d / "composer.json").write_text(keep[0].replace('"drupal/core-recommended": "^12"', '"drupal/core-recommended": "12.0.0-beta1"'))
        print(safe20_composer(site, "update", "drupal/core-*", "--with-all-dependencies")[-3000:])
        print(safe20_composer(site, "update", "drupal/core-*", "--with-all-dependencies", "--no-blocking")[-1500:])
        drush(site, "updatedb", "-y")
        drush(site, "cache:rebuild")
        safe20_check(page, url)
        snap("20-core-security-update-required")
        page.goto(url + "/admin/reports/status")
        page.wait_for_load_state("networkidle")
        scroll_to(page, ":text('Drupal core update status')", 200)
        snap("20-core-status-report-security")
    finally:
        (d / "composer.json").write_text(keep[0])
        (d / "composer.lock").write_text(keep[1])
        subprocess.run(["ddev", "composer", "install"], cwd=d, check=True, capture_output=True)
        drush(site, "updatedb", "-y")
        drush(site, "cache:rebuild")

    safe20_check(page, url)
    page.goto(url + "/admin/config/development/maintenance")
    page.wait_for_load_state("networkidle")
    page.check("input[name='maintenance_mode']")
    page.fill("textarea[name='maintenance_mode_message']", "Lens & Trail is being updated. Back in a few minutes.")
    snap("20-core-maintenance")
    safe20_restore(site)


def safe20_cms_steps(page: Page, site: dict, snap) -> None:
    """Chapter 20 on Drupal CMS: core 11.4.11 to 11.4.12 from the browser, unattended updates, Backup and Migrate."""
    url = site["url"]
    safe20_restore(site)
    log_in(page, site)
    page.set_default_timeout(300000)
    safe20_check(page, url)
    snap("20-cms-available-updates")
    page.goto(url + "/admin/reports/updates/update")
    page.wait_for_load_state("networkidle")
    if page.locator("input[value='Delete existing update']").count():
        page.locator("input[value='Delete existing update']").first.click()
        page.wait_for_load_state("networkidle")
        page.goto(url + "/admin/reports/updates/update")
        page.wait_for_load_state("networkidle")
    snap("20-cms-update-form")
    page.click("#automatic-updates-updater-form #edit-submit")
    page.wait_for_timeout(3000)
    snap("20-cms-downloading")
    page.get_by_text("Ready to update").first.wait_for(timeout=900000)
    page.wait_for_load_state("networkidle")
    snap("20-cms-ready")
    page.locator("input[type='submit'][value='Continue'], button:has-text('Continue')").first.click()
    for _ in range(180):
        page.wait_for_timeout(5000)
        if "/batch" not in page.url and not page.get_by_text("Ready to update").count():
            break
    page.wait_for_load_state("networkidle")
    print("--- After the update: " + page.url + "\n" + page.locator("main").first.inner_text()[:1500])
    snap("20-cms-updated")
    page.goto(url + "/admin/reports/updates/settings")
    page.wait_for_load_state("networkidle")
    snap("20-cms-unattended")
    composer(site, "require", "drupal/backup_migrate")
    drush(site, "pm:install", "backup_migrate", "-y")
    page.goto(url + "/admin/config/development/backup_migrate")
    page.wait_for_load_state("networkidle")
    snap("20-cms-backup-migrate")
    safe20_restore(site)


def safe20_d11_steps(page: Page, site: dict, snap) -> None:
    """Chapter 20 on the Drupal 11 site: Available updates, and Upgrade Status."""
    url = site["url"]
    safe20_restore(site)
    log_in(page, site)
    safe20_check(page, url)
    snap("20-d11-available-updates")
    page.goto(url + "/admin/reports/upgrade-status", timeout=300000)
    page.wait_for_load_state("networkidle")
    print("--- Upgrade Status\n" + page.locator("main").first.inner_text()[:4000])
    snap("20-d11-upgrade-status")


CONFIG21_SYNC = "$settings['config_sync_directory'] = '../config/sync';"


def config21_settings(site: dict) -> None:
    """Points the site's sync folder to ../config/sync, as Chapter 21 does by hand (settings.php isn't in the snapshots)."""
    f = Path(site["dir"]) / "web/sites/default/settings.php"
    text = f.read_text()
    if CONFIG21_SYNC not in text:
        text = text.replace("# $settings['config_sync_directory'] = '/directory/outside/webroot';", CONFIG21_SYNC)
        f.write_text(text)


def config21_live(core: dict, live: dict) -> None:
    """Makes the live copy what Chapter 21 makes it: a clone of the club's site, with an empty sync folder.

    The folder is copied once (the way the chapter does it); after that, only the database is copied again.
    """
    d = Path(live["dir"])
    if not d.exists():
        shutil.copytree(core["dir"], d, symlinks=True, ignore=shutil.ignore_patterns("db_snapshots"))
        subprocess.run(["ddev", "config", "--project-name=" + d.name], cwd=d, check=True, capture_output=True)
    subprocess.run(["ddev", "start"], cwd=d, check=True, capture_output=True)
    dump = d.parent / "lens-and-trail-chapter21.sql.gz"
    subprocess.run(["ddev", "export-db", "--file=" + str(dump)], cwd=core["dir"], check=True, capture_output=True)
    subprocess.run(["ddev", "import-db", "--file=" + str(dump)], cwd=d, check=True, capture_output=True)
    dump.unlink()
    config21_settings(live)
    shutil.rmtree(d / "config", ignore_errors=True)
    (d / "config/sync").mkdir(parents=True)
    drush(live, "cache:rebuild")


def config21_steps(page: Page, site: dict, snap) -> None:
    """Chapter 21: the sync folder, single and full export on the club's site, full import on the live copy."""
    url = site["url"]
    live = SITES["live"]
    d = Path(site["dir"])
    subprocess.run(["ddev", "snapshot", "restore", "ch20-start"], cwd=d, check=True, capture_output=True)
    config21_live(site, live)
    log_in(page, site)

    # The sync folder: settings.php points outside the web folder, which doesn't exist yet.
    config21_settings(site)
    shutil.rmtree(d / "config", ignore_errors=True)
    drush(site, "cache:rebuild")
    page.goto(url + "/admin/reports/status")
    page.wait_for_load_state("networkidle")
    scroll_to(page, ":text('Configuration sync directory')", 200)
    snap("21-sync-missing")
    (d / "config/sync").mkdir(parents=True)

    # One item: the Hike content type.
    page.goto(url + "/admin/config/development/configuration/single/export")
    page.wait_for_load_state("networkidle")
    page.select_option("select[name='config_type']", "node_type")
    page.wait_for_timeout(1500)
    page.select_option("select[name='config_name']", "hike")
    page.wait_for_timeout(1500)
    snap("21-single-export")

    # The change: an Elevation gain field on Hike.
    def elevation_settings(p: Page) -> None:
        p.locator(".ui-dialog").get_by_label("Minimum").fill("0")
        p.locator(".ui-dialog").get_by_label("Suffix").fill(" m")
    create_field(page, url + "/admin/structure/types/manage/hike/fields", "Number", "Elevation gain", "Integer", elevation_settings)

    # Full export.
    page.goto(url + "/admin/config/development/configuration/full/export")
    page.wait_for_load_state("networkidle")
    snap("21-full-export")
    with page.expect_download() as download:
        page.locator("main input[type='submit']").first.click()
    archive = Path(site["dir"]).parent / download.value.suggested_filename
    download.value.save_as(str(archive))

    # On the live copy: Morag made an image style there, then the upload.
    drush_php(live, "\\Drupal\\image\\Entity\\ImageStyle::create(['name' => 'square', 'label' => 'Square'])->save();")
    context = page.context.browser.new_context(viewport={"width": WIDTH, "height": 1000}, device_scale_factor=2, ignore_https_errors=True)
    lp = context.new_page()
    lp.set_default_timeout(300000)
    log_in(lp, live)
    lp.goto(live["url"] + "/admin/config/development/configuration/full/import")
    lp.wait_for_load_state("networkidle")
    lp.set_input_files("input[type='file']", str(archive))
    save(lp, "21-full-import")
    lp.locator("main input[type='submit']").first.click()
    lp.wait_for_load_state("networkidle")
    archive.unlink()
    print("--- Synchronize\n" + lp.locator("main").first.inner_text()[:2000])
    lp.set_viewport_size({"width": WIDTH, "height": 1450})
    save(lp, "21-synchronize")
    lp.set_viewport_size({"width": WIDTH, "height": 1000})
    lp.locator("tr:has-text('field.storage.node.field_elevation_gain') a:has-text('View differences')").click()
    lp.wait_for_selector(".ui-dialog")
    lp.wait_for_timeout(1500)
    save(lp, "21-differences")
    lp.locator(".ui-dialog-titlebar-close").click()
    lp.locator("tr:has-text('image.style.square') a:has-text('View differences')").click()
    lp.wait_for_selector(".ui-dialog")
    lp.wait_for_timeout(1500)
    save(lp, "21-differences-deleted")
    lp.locator(".ui-dialog-titlebar-close").click()
    lp.locator("input[type='submit'][value='Import all']").click()
    lp.wait_for_url("**/admin/config/development/configuration", timeout=300000)
    lp.wait_for_load_state("networkidle")
    save(lp, "21-imported")
    lp.goto(live["url"] + "/admin/structure/types/manage/hike/fields")
    lp.wait_for_load_state("networkidle")
    save(lp, "21-live-fields")
    context.close()

    # The checklist.
    page.goto(url + "/admin/config/system/cron")
    page.wait_for_load_state("networkidle")
    snap("21-cron")
    page.goto(url + "/admin/config/development/performance")
    page.wait_for_load_state("networkidle")
    snap("21-performance")
    drush(site, "config:export", "-y")
    subprocess.run(["ddev", "snapshot", "--cleanup", "--name", "ch21-done", "-y"], cwd=d, capture_output=True)
    subprocess.run(["ddev", "snapshot", "--name", "ch21-done"], cwd=d, check=True, capture_output=True)


SEQUENCES = [
    ("core", config21_steps, 1280, ["21-sync-missing", "21-single-export", "21-full-export", "21-full-import", "21-synchronize", "21-differences", "21-differences-deleted", "21-imported", "21-live-fields", "21-cron", "21-performance"]),
    ("core", safe20_core_steps, 1280, ["20-core-available-updates", "20-core-update-settings", "20-core-up-to-date", "20-core-security-update-required", "20-core-status-report-security", "20-core-maintenance"]),
    ("cms", safe20_cms_steps, 1440, ["20-cms-available-updates", "20-cms-update-form", "20-cms-downloading", "20-cms-ready", "20-cms-updated", "20-cms-unattended", "20-cms-backup-migrate"]),
    ("d11", safe20_d11_steps, 1280, ["20-d11-available-updates", "20-d11-upgrade-status"]),
    ("cms", ai19_anthropic_steps, 1440, ["19-cms-anthropic", "19-cms-ai-settings", "19-cms-anthropic-chatbot-tags", "19-cms-anthropic-page"]),
    ("cms", ai19_cms_steps, 1440, ["19-cms-recommended", "19-cms-provider", "19-cms-ai-dashboard", "19-cms-chatbot-consent", "19-cms-chatbot-tags", "19-cms-tags", "19-cms-chatbot-field", "19-cms-media-fields", "19-cms-alt-settings", "19-cms-alt-consent", "19-cms-alt-generated", "19-cms-canvas-ai-prompt", "19-cms-canvas-ai-page", "19-cms-canvas-ai-facts", "19-cms-review-changes", "19-cms-translate-ai"]),
    ("cms", i18n18_cms_steps, 1440, ["18-cms-content-language", "18-cms-translate-dashboard", "18-cms-translate-editor", "18-cms-translate-review", "18-cms-es-join"]),
    ("core", i18n18_setup_steps, 1280, ["18-extend", "18-add-language", "18-languages", "18-detection", "18-url-prefixes", "18-switcher-block", "18-es-front-interface", "18-content-language", "18-pattern-es", "18-patterns", "18-translations-about", "18-translate-about", "18-translate-hike", "18-aliases", "18-content"]),
    ("core", i18n18_views_steps, 1280, ["18-es-hikes-twice", "18-views-default-translation", "18-views-rendering-language", "18-es-hikes"]),
    ("core", i18n18_config_steps, 1280, ["18-config-translation", "18-translate-view", "18-interface-translation", "18-es-front", "18-es-hike", "18-es-join"]),
    ("core", i18n18_people_steps, 1280, ["18-translator-permissions", "18-lucia-translate", "18-translations-lucia"]),
    ("cms", seo17_cms_steps, 1440, ["17-cms-patterns", "17-cms-metatag", "17-cms-metatag-node", "17-cms-social-style", "17-cms-seo-fields", "17-cms-realtime-seo", "17-cms-tips", "17-cms-seo-checklist"]),
    ("core", seo17_steps, 1280, ["17-extend", "17-token-browser", "17-pattern-hike", "17-pattern-areas", "17-patterns", "17-pathauto-settings", "17-bulk", "17-aliases", "17-term-alias", "17-hike-alias", "17-redirects", "17-404", "17-sitemap-settings", "17-sitemap"]),
    ("core", themes16_twig_steps, 1280, ["16-development-settings"]),
    ("cms", themes16_cms_steps, 1440, ["16-cms-appearance", "16-cms-mercury-settings", "16-cms-mercury", "16-cms-olivero", "16-cms-tara", "16-cms-byte"]),
    ("core", themes16_steps, 1280, ["16-appearance", "16-stark", "16-appearance-solo", "16-solo", "16-solo-settings", "16-solo-blocks", "16-uninstall-solo", "16-olivero-global", "16-olivero-color", "16-olivero-logo", "16-olivero-club", "16-admin-theme", "16-default-admin-settings"]),
    ("cms", cms_easy_breadcrumb_steps, 1440, ["14-cms-easy-breadcrumb"]),
    ("core", members15_steps, 1280, ["appendix-c-members-block", "appendix-c-members-access", "appendix-c-members-view", "appendix-c-members-page", "appendix-c-members-denied"]),
    ("core", users15_more_steps, 1280, ["15-user-fields", "15-profile", "15-timezones", "15-hike-leader-field", "15-leader-draft", "15-secretary-content", "15-secretary-publish"]),
    ("core", users15_captcha_steps, 1280, ["15-extend-captcha", "15-captcha-points", "15-register-captcha"]),
    ("core", users15_registration_steps, 1280, ["15-account-settings", "15-register", "15-register-done", "15-mailpit", "15-people-blocked", "15-activate", "15-unapproved", "15-bulk-role"]),
    ("core", users15_roles_steps, 1280, ["15-people", "15-add-role", "15-roles", "15-permissions-member", "15-permissions-transitions", "15-permissions-all", "15-add-user", "15-people-after"]),
    ("core", views2_album_count_steps, 1280, ["appendix-c-count-duplicates", "appendix-c-group-column", "appendix-c-album-count"]),
    ("cms", cms_page_template_steps, 1440, ["14-cms-page-template"]),
    ("core", menus14_steps, 1280, ["14-menus", "14-main-menu", "14-add-link", "14-expanded", "14-dropdown", "14-footer-menu", "14-footer-menu-visitor", "14-breadcrumb"]),
    ("core", blocks14_content_steps, 1280, ["14-block-types", "14-club-info-fields", "14-add-club-info", "14-footer-top", "14-content-blocks", "14-visibility-roles", "14-sidebar-visitor", "14-footer"]),
    ("core", blocks14_steps, 1280, ["14-block-layout", "14-regions", "14-place-block", "14-configure-block", "14-visibility-pages", "14-sidebar"]),
    ("core", views2_answer_steps, 1280, ["appendix-c-next-hike-attachment", "appendix-c-offset", "appendix-c-easy"]),
    ("core", views2_displays_steps, 1280, ["13-add-display", "13-display-actions", "13-views-settings"]),
    ("core", views2_more_steps, 1280, ["13-attachment", "13-archive-attachment", "13-feed", "13-feed-icon", "13-caching", "13-sql"]),
    ("core", views2_contextual_steps, 1280, ["13-term-before", "13-term-view", "13-depth", "13-header-target", "13-term-after", "13-default-argument", "13-hike-albums", "13-menu-tab", "13-user-hikes", "13-summary", "13-archive"]),
    ("core", views2_hike_admin_steps, 1280, ["13-rewrite", "13-leader-field", "13-hike-admin"]),
    ("core", views2_albums_steps, 1280, ["13-first-photo", "13-hike-relationship", "13-galleries", "13-duplicates"]),
    ("core", views2_fields_steps, 1280, ["13-field-thumbnail", "13-table-settings", "13-reverse-relationship", "13-photo-credits", "13-use-aggregation", "13-aggregation-count", "13-photographers"]),
    ("core", views_steps, 1280, ["12-views-list", "12-add-view", "12-view-edit", "12-filter-date", "12-no-results", "12-view-filtered", "12-hikes-page", "12-block-override", "12-block-card", "12-more-link", "12-exposed-filter", "12-hikes-easy", "12-grid-settings", "12-lb-choose-block", "12-front-page", "12-galleries"]),
    ("core", reuse_field_steps, 1280, ["07-reuse-field", "07-reuse-settings"]),
    ("core", layout_builder_steps, 1600, ["08-lb-start", "08-lb-choose-layout", "08-lb-column-widths", "08-lb-choose-block", "08-lb-content-block", "08-lb-body-block", "08-lb-remove-section", "08-lb-save"]),
    ("core", manage_display_steps, 1280, ["08-hike-before", "08-display-overview", "08-display-default", "08-display-order", "08-display-labels", "08-display-distance", "08-display-hike-leader", "08-date-format", "08-display-date", "08-hike-after", "08-display-teaser", "08-view-mode-add", "08-display-card"]),
    ("core", hike_layout_exercise, 1280, ["08-exercise-hike-layout"]),
    ("core", media_install_steps, 1280, ["09-extend-media", "09-media-types", "09-license-settings", "09-image-fields", "09-image-form-media-library", "09-add-image", "09-media-list"]),
    ("core", photo_field_steps, 1280, ["09-photo-field-type", "09-photo-field-settings", "09-media-library", "09-hike-form-photo", "09-hike-photo-large"]),
    ("core", image_styles_steps, 1280, ["09-image-styles", "09-image-style-banner", "09-media-banner-display", "09-hike-photo-view-mode", "09-hike-banner", "09-responsive-style", "09-media-banner-responsive", "09-hike-phone"]),
    ("core", media_editor_steps, 1280, ["09-library-upload", "09-text-format-media", "09-editor-media"]),
    ("core", widgets_formatters_steps, 1280, ["09-photo-widget", "09-photo-formatters", "09-photo-thumbnail-settings", "09-hike-thumbnail"]),
    ("core", gallery_steps, 1280, ["09-gallery-fields", "09-gallery-upload", "09-gallery-page"]),
    ("core", taxonomy_areas_steps, 1280, ["10-add-vocabulary", "10-add-term", "10-areas-drag", "10-areas-overview"]),
    ("core", taxonomy_fields_steps, 1280, ["10-area-fields", "10-term-pentland-hills", "10-area-field-settings", "10-hike-form-area", "10-hike-area", "10-term-turnhouse-hill"]),
    ("core", taxonomy_themes_steps, 1280, ["10-themes-field-settings", "10-media-themes", "10-photo-themes"]),
    ("core", modules_steps, 1280, ["11-extend-diff", "11-revisions-compare", "11-diff", "11-project-browser", "11-pb-commands", "11-module-filter", "11-pb-recipes", "11-reuse-comment", "11-gallery-comments"]),
    ("cms", cms_modules_steps, 1280, ["11-cms-pb-install", "11-cms-pb-installed", "11-cms-devel-generate", "11-cms-generated"]),
    ("cms", canvas_steps, 1600, ["08-canvas-page-data", "08-canvas-heading", "08-canvas-grid", "08-canvas-text", "08-canvas-move", "08-canvas-card", "08-canvas-publish"]),
]


def matches(name: str, wanted: list[str]) -> bool:
    return not wanted or any(name == w or name.startswith(w + "-") for w in wanted)


def save(page: Page, name: str, full_page: bool = False, element: str | None = None) -> None:
    """Save a screenshot, at the same scale as the others (one image pixel per CSS pixel).

    With element, only that part of the page (a dialog, say) is saved.
    """
    target = IMAGES / f"{name}.png"
    if element:
        box = page.locator(element).first
        width = round(box.bounding_box()["width"])
        box.screenshot(path=str(target))
    else:
        width = WIDTH
        page.screenshot(path=str(target), full_page=full_page)
    subprocess.run(["sips", "--resampleWidth", str(width), str(target)], check=True, capture_output=True)
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
            try:
                steps(page, site, lambda name, element=None: save(page, name, element=element))
            except Exception:
                if os.environ.get("DEBUG_SHOT"):
                    page.screenshot(path=os.environ["DEBUG_SHOT"])
                raise
            context.close()
        browser.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
