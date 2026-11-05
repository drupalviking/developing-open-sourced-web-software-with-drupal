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


def as_visitor(page: Page, site: dict, path: str, name: str) -> None:
    """A full-page screenshot of path, logged out, in a window of its own."""
    context = page.context.browser.new_context(viewport={"width": WIDTH, "height": 1000}, device_scale_factor=2, ignore_https_errors=True)
    visit = context.new_page()
    visit.goto(site["url"] + path)
    visit.wait_for_load_state("networkidle")
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
SEQUENCES = [
    ("core", reuse_field_steps, 1280, ["07-reuse-field", "07-reuse-settings"]),
    ("core", layout_builder_steps, 1600, ["08-lb-start", "08-lb-choose-layout", "08-lb-column-widths", "08-lb-choose-block", "08-lb-content-block", "08-lb-body-block", "08-lb-remove-section", "08-lb-save"]),
    ("core", manage_display_steps, 1280, ["08-hike-before", "08-display-overview", "08-display-default", "08-display-order", "08-display-labels", "08-display-distance", "08-display-hike-leader", "08-date-format", "08-display-date", "08-hike-after", "08-display-teaser", "08-view-mode-add", "08-display-card"]),
    ("core", hike_layout_exercise, 1280, ["08-exercise-hike-layout"]),
    ("core", media_install_steps, 1280, ["09-extend-media", "09-media-types", "09-license-settings", "09-image-fields", "09-image-form-media-library", "09-add-image", "09-media-list"]),
    ("core", photo_field_steps, 1280, ["09-photo-field-type", "09-photo-field-settings", "09-media-library", "09-hike-form-photo", "09-hike-photo-large"]),
    ("core", image_styles_steps, 1280, ["09-image-styles", "09-image-style-banner", "09-media-banner-display", "09-hike-photo-view-mode", "09-hike-banner", "09-responsive-style", "09-media-banner-responsive", "09-hike-phone"]),
    ("core", media_editor_steps, 1280, ["09-library-upload", "09-text-format-media", "09-editor-media"]),
    ("core", gallery_steps, 1280, ["09-gallery-fields", "09-gallery-upload", "09-gallery-page"]),
    ("core", taxonomy_areas_steps, 1280, ["10-add-vocabulary", "10-add-term", "10-areas-drag", "10-areas-overview"]),
    ("core", taxonomy_fields_steps, 1280, ["10-area-fields", "10-term-pentland-hills", "10-area-field-settings", "10-hike-form-area", "10-hike-area", "10-term-turnhouse-hill"]),
    ("core", taxonomy_themes_steps, 1280, ["10-themes-field-settings", "10-media-themes", "10-photo-themes"]),
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
