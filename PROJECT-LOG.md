# Project log

Decisions, history, and open items for the book. `README.md` has the layout, the commands, and
the chapter status. Keep both up to date at the end of every chapter.

Last updated: 2026-11-05.

## Where we are

Read this first when picking the work up in a new session.

- **Done and reviewed:** the Preface and Chapters 1 to 5 (Chapter 5 on 2026-11-05). Waiting for the author: Appendix B's new section "How Drupal's code has changed", and the author's own stories in Chapters 2 and 3 (`%%` placeholders).
- **Waiting for the author's review: Chapter 6, *Your First Page*** (drafted 2026-11-05, on `documentation/chapter-06-your-first-page`). Next after the review: Chapter 7, *Everything Is an Entity*, which already has a draft (it uses Drupal CMS screenshots and Basic page; on core, Basic page now comes from Chapter 6).
- **The test sites** (DDEV, outside this repository; on the author's machine DDEV's router uses port 8443, because 443 is taken):
  - `~/websites/open-university/lens-and-trail`: Drupal 12.0.0-beta2, the club's site in the state Chapter 5 leaves it (see "The photo club site"). `https://lens-and-trail.ddev.site:8443`, `admin` / `12345`. Drush is `14.x-dev`, with `minimum-stability: dev` and `prefer-stable: true` in `composer.json`, because no released Drush supports Drupal 12 yet.
  - `~/websites/open-university/lens-and-trail-cms`: Drupal CMS 2.2.8 on Drupal 11.4.11, Starter template. `https://lens-and-trail-cms.ddev.site:8443`, `admin@lens-and-trail-cms.ddev.site` / `12345`. Project Browser's **Recipes** source was turned on for a test (it's off by default in Drupal CMS); the failed Basic page recipe left nothing behind.
- **Screenshots**: `tools/screenshots.py` (Python Playwright in `.venv`, with Playwright's own Chromium; see the README) takes Chapter 6's, 1280 pixels wide (at 2x, resized with `sips --resampleWidth 1280`). It only looks at the sites, so a screenshot shows the site as it is now: Chapter 6's content form already shows the moderation fields, because moderation is installed later in the chapter. Chapters 4 and 5 were taken with throwaway scripts driving Brave, and still need adding (see Open items). For finding your way around a screen, a small driver in the session's scratchpad (log in, run steps, print the page's text, screenshot) worked well.
- **Other work outside this repository:** the course material in `~/websites/open-university/what-is-open-source/` (not in Git; its `BACKLOG.md` has the open items).

## How we work

- **The author** (Hilmar Kári Hallbjörnsson) decides what goes in, reviews every chapter, and
  pushes and merges. Claude drafts, builds, and commits.
- **One chapter at a time.** Before drafting a chapter, Claude asks the author questions about what
  to include and leave out ("grilling"). The author reviews the draft before the next chapter starts.
- **Branches**: one branch per unit of work, created only after the author says yes in the
  conversation. Claude never commits to `main`, pushes, opens pull requests, or merges.
- **After a merge** the author deletes the local branch. A new chapter branch starts from an up-to-date `main`
  (check `git fetch` and `main...origin/main` first).
- **No Claude attribution** in commit messages (no `Co-Authored-By` or "Generated with" lines). The author's
  rule, 2026-11-04.
- **Chapter numbers and cross-references** are checked once, at the end.

## Decisions

Made on 2026-11-04, at the start of the rewrite.

| Question | Decision |
|---|---|
| Audience | People who have never seen Drupal. "Basic CS knowledge" only means being able to use a terminal to install things. |
| Scope | Site building only. Module development belongs to the companion book (`websites/ru/book-rewrite`), and this book points to it at the end. |
| Drupal core vs. Drupal CMS | Equal weight, leaning slightly towards core: Drupal CMS is a product built on core, and the reader should understand what's underneath. Where they differ, show both. |
| Canvas vs. Layout Builder | Teach both, as two approaches. Drupal CMS pushes Canvas; many developers prefer Layout Builder or field-based displays. Building your own Canvas component is in the backlog as an advanced section. |
| Example | One running site, built up chapter by chapter: a small photography club that also goes hiking. |
| Teachers' kit | Yes, alongside the book: for Drupal in a Day, for university courses, and for self-study. Every chapter ends with exercises. |
| License | CC BY-SA 4.0 (was GPLv3). The only commit by anyone other than the author (einardarri, 2025) fixed image markup, not prose. |
| Output | Markdown in `book/` for now. PDF/EPUB later. |
| Structure of a Drupal System | Moved to Appendix B. Too technical for chapter 1. |
| New topics | Configuration management (export/import, going live) and AI in Drupal CMS both get chapters. |
| Spelling | US. |
| The club (2026-11-04) | **Lens & Trail**, a photography and hiking club in **Edinburgh**, Scotland. Aimed at a European readership. |
| Languages (2026-11-04) | English and **Spanish** (not Icelandic: few readers would be). Story: many members are from Spain and Latin America. |
| Build on (2026-11-04) | **Drupal core first**: the club site is built on core; Drupal CMS appears in "On Drupal CMS" boxes. |
| Drupal version (2026-11-04) | **Drupal 12** (12.0.0 and 11.5.0 are released together in the week of 7 December 2026; rc1 the week of 9 November). The Preface says 11.5 readers can follow along. The test site is built on 12. For each contributed module a chapter uses, check that it has a Drupal 12 release; if not, say so in the chapter. |
| Admin theme (2026-11-04) | Core's **Default Admin** (built from Gin): experimental in 11.4, stable and Standard's admin theme in 11.5/12. Every admin screenshot uses it. |
| Photos (2026-11-04) | Openly licensed photos (compatible with CC BY-SA 4.0, credited) for what the reader sees, and Devel Generate for bulk test content. Taught in the book: see the backlog. |
| Emoticons (2026-11-04) | Keep them: the author uses them a lot, and they make the tone personal. |
| WordPress (2026-11-04) | A comparison, **never a contest**. One translation table in Chapter 1 ("Coming from WordPress?") with a Drupalism box on *plugin* and *block*; later, a `> **Coming from WordPress?**` box only where WordPress knowledge would mislead or help (see the backlog), never as a ritual at the start of every chapter. |
| Theme file structure | Moved from Chapter 1 to Chapter 14 (`manuscript/14-appearance.md`), where it'll be reworked. |
| Numbers (2026-11-04) | Versions and support dates that change are placeholders, `{{ number:name }}`, filled from `data/numbers.yml`, which `tools/update_numbers.py` updates from each number's source (the author's idea, as in the `what-is-open-source` course material). |
| Article and Page (2026-11-04) | Drupal 11.4's Standard profile no longer creates them (#3587118, change record node/3590571; checked on 11.4.11: a fresh Standard install has no content types), and Drupal 12 also removes core's `page_content_type` and `article_content_type` recipes. The author's choice: **Chapter 6** has the reader build **Basic page** by hand (name, description, body field), on 11.4, 11.5 and 12 alike; no recipe box, and no Project Browser route (the author dropped it on 2026-11-04). Why, from the tests on 2026-11-04: on core, Project Browser lists the recipe but only shows **View Commands** (installing from the browser needs Automatic Updates' Package Manager), and the command it shows, `php core/scripts/drupal recipe`, is deprecated in 11.4 and fails in the `recommended-project` layout; on Drupal CMS the recipe fails, because Utility page already has the machine name `page`. **Chapter 10** writes a small Lens & Trail recipe in `examples/recipes/` that creates the same Basic page, and applies it with `ddev drush recipe`, to show what recipes are for. |
| Front-end theme (2026-11-04) | Drupal 12 has no front-end theme in core (Olivero and Claro moved to contrib; core keeps Default Admin, Stark and Starterkit). **Chapter 4** installs Olivero with `ddev composer require drupal/olivero` and sets it as the default theme; Default Admin stays the admin theme. Switch to Mercury when it has a stable Drupal 12 release (see the backlog). |
| Drush (2026-11-04) | Chapter 4 adds it with `ddev composer require drush/drush` (`drupal/recommended-project` doesn't include it). No released Drush supports Drupal 12 yet (13.x needs Guzzle 7); the test site runs 14.x-dev. |
| Markdown (2026-11-04) | One line per paragraph in new text: Obsidian shows hard line breaks. |

## History

- **2026-11-04**: Moved the Obsidian drafts (`1. preface/` … `Appendix b - Q and A/`) into
  `manuscript/NN-slug.md` and the screenshots into `manuscript/images/NN-what.png`, keeping git
  history. Content types and Fields became Chapter 7; Media, Taxonomy, and Users went to Chapters 8,
  9, and 13; Development tools and Installing Xdebug became Appendix A; Structure of a Drupal System
  became Appendix B. The developer Q&A (attributes, hooks, module directory structure, the Spotify
  refactoring) went to `archive/developer-qa/`, out of the build. Obsidian `![[...]]` image links
  became Markdown links. `Book outline.md` was replaced by the contents table in the README.
  Added `tools/build.py`, this log, the `write-chapter` skill, and the CC BY-SA 4.0 license.
  The empty `recipe.yml` and `composer.json` in the root (never in git) were deleted.
- **2026-11-04**: Drafted the Preface (who it's for, the three readers, what each chapter covers, the club,
  core vs. Drupal CMS, conventions, contributing) and rewrote Chapter 1 from "Where do I begin?": kept the
  author's opening, CMS section, and building-block texts; added the static-site example on the club, what
  Drupal is, core vs. Drupal CMS with a Drupalism box, the Lens & Trail site and a chapter-by-chapter table,
  configuration vs. content, summary, five exercises, and verified links.
- **2026-11-04**: The author reviewed Chapter 1. From the review: the Preface targets Drupal 12 (11.5 readers
  welcome); Default Admin is stable in 11.5 and 12; chapter pointers are full sentences ("We also cover fields in
  Chapter 7"), now a rule in the skill; a "Coming from WordPress?" translation table and Drupalism box, with
  later boxes in the backlog. The author also reviewed the Preface.
- **2026-11-04**: Drafted Chapter 2 (the author's choices: GPL mostly, a table of other licenses; who makes
  Drupal here, how to join in Chapter 20; the author's own story later). Facts from drupal.org's Licensing FAQ
  (GPLv2 or later; viewing a site isn't distributing; selling under the GPL; drupal.org content is CC BY-SA 2.0)
  and Drupal Association page (nonprofit, runs drupal.org, funding; Dries owns the trademark). Credit system
  since 2015; the Drupal Certified Partners list is ranked by credit. Reviewed by the author the same day: the
  "Can I...?" table is right, and the Drupal Association supports DrupalCon but doesn't run it everywhere.
- **2026-11-04**: Rewrote Chapter 3 with the author's answers: a story for site builders, era by era, with a release table, deprecation explained with roads, Starshot and Drupal CMS, Drupal 12, and how to read version numbers. The programmers' material (hooks, the Form API, theming, Drupal 7's and 8's code, the deprecation example, the upgrade tools) moved to a new section of Appendix B. Fixed from the draft: Drupal 8 on 19 November 2015 (Dries's birthday); fields came with CCK, in core from Drupal 7; the menu rewrite was Drupal 6; FCKeditor was never in core; the last 8.x was 8.9.20; `.info.yml`; CMI; Starshot in 2024. Added `data/numbers.yml`, `tools/update_numbers.py` and `{{ number:... }}` placeholders to the build. The author's review: Drupal 11 needed more than the new admin menu, so the chapter now lists its minor releases 11.1 to 11.5 (from drupal.org's 11.1, 11.3 and 11.4 release posts); the exercise that looked for a live Drupal 7 site was dropped as snooping.
- **2026-11-04**: Rewrote Chapter 4 with the author's answers: DDEV only (per-OS install with DDEV's docs, `ddev --version`), Composer in two sentences (the rest moved to a Chapter 10 stub), the `lens-and-trail` project on Drupal 12 with Drush, the browser installer as the main path with a `ddev drush site:install` box, every Configure site field explained (the site email is the From address), the `settings.php` warning, a first look (no content types, no front-end theme, Access denied for visitors), Olivero from contrib, `ddev drush uli`, starting and stopping, Drupal CMS 2.2.8 (three installer screens, Starter), the Launcher and Drupal Forge, troubleshooting, five exercises. Checked on test sites with Drupal 12.0.0-beta2, Drupal CMS 2.2.8 and core 11.4.11; the screenshots are from them (taken with Playwright, not yet with `tools/screenshots.sh`). The Lando section was dropped (Appendix A).
- **2026-11-04**: Rewrote Chapter 5 with the author's answers: a tour of the Navigation sidebar on the Drupal 12 site, item by item, with the chapter that covers each (a table for Structure); Help as the built-in manual; user 1 in a paragraph (details in Chapter 13); an "On Drupal CMS" box (Dashboard, Pages, Media, Trash, Tools, Gin); Basic site settings (slogan) and Regional settings (United Kingdom, Monday); the site side: the top bar, contextual links on the Site branding block, and the logged-out view; five exercises. The raw SVG headings are gone. Checked on the Drupal 12.0.0-beta2 and Drupal CMS 2.2.8 test sites; screenshots from them.
- **2026-11-05**: The author reviewed Chapter 5. Drupal 11's and 12's support dates updated from PSA-2026-11-02 (December 2028 and December 2030; minor versions get 8 months of security support from 2027), found in the test site's Announcements; Chapter 3's 11.5 bullet now uses the placeholder.
- **2026-11-05**: Added a backlog item: how the book is written with AI assistance and kept up to date (the author's request; probably in the Preface).
- **2026-11-05**: Drafted Chapter 6 with the author's answers: Layout Builder on the core site and Canvas in an "On Drupal CMS" box (Canvas has no Drupal 12 release); revisions, the URL alias and menu link, content moderation, and Trash (with a note that core readers can install it, since it supports Drupal 12); a *Welcome* Basic page as the front page. "Promoted to front page": the author asked for evidence on whether anyone uses it; there are no usage figures, core renamed it **Promoted** (#3593281) and kept the fields (#3538655, won't fix), and Drupal 12 hides it from new content types' forms, so the chapter explains it as a "featured" flag for lists (Chapter 11) and leaves it off. Built on the test sites, step by step, and wrote `tools/screenshots.py` for the chapter's twelve screenshots. Added `canvas_version` to `data/numbers.yml`.

## The photo club site

What each chapter adds to the Lens & Trail site. Later chapters and exercises must not contradict it.

| Chapter | Adds |
|---|---|
| 1 | Introduces the club and what its site needs: hikes, photos, galleries, members, news, pages, categories (places, photo themes), English and Spanish; roles: visitor, member, hike leader, secretary, administrator. Exercise 4 (who does what) is reused in Chapter 13; Exercise 5 (model a hike) is compared with Chapter 7. Also: the WordPress translation table. |
| 2 | Nothing built. The committee's questions (why Drupal, who's behind it, what's the catch) frame the chapter; Exercise 4 (commercial builder vs. Drupal) and Exercise 5 (a CC BY-SA photo of the Pentland Hills on a poster) set up Chapter 8's photo licensing. |
| 3 | Nothing built. |
| 4 | The DDEV project `lens-and-trail` (`https://lens-and-trail.ddev.site`) on Drupal 12, with Drush. Site name "Lens & Trail", site email `hello@lens-and-trail.ddev.site`, admin `admin` / `12345` (`admin@lens-and-trail.ddev.site`), time zone London. No content types; Olivero (contrib) is the default theme, Default Admin the admin theme; the front page is still `/admin/welcome` (Access denied for visitors) until Chapter 6. Optional second project `lens-and-trail-cms`: Drupal CMS with the Starter template, `admin@lens-and-trail-cms.ddev.site` / `12345`. |
| 5 | Slogan "Photos and hikes around Edinburgh" (shown by Olivero's Site branding block); Regional settings: default country United Kingdom, first day of week Monday, time zone London. Front page and error pages unchanged (Chapter 6 sets the front page). |
| 6 | Content type **Basic page** (machine name `page`; description; no author and date; Main navigation; Promoted and Sticky off), with a **Body** field (`field_body`, Formatted text, Long text), label hidden. Pages: node 1 *About the club* (`/about`, menu link *About*, weight 1; revisions: night walks, then a draft "around forty members", published), node 2 *How to join* (`/join`, menu link *Join us*, weight 2; its own Layout Builder layout: 67%/33%, body left, an inline block *When and where* with the meeting times right), node 3 *Welcome to Lens & Trail* (`/welcome`, no menu link). Front page `/node/3`. Layout Builder on for Basic page, with per-page layouts. Content Moderation and Workflows installed; the **Editorial** workflow applies to Basic page. Meeting times: hikes every other Saturday at 9:30, photo evenings the first Thursday of the month at 19:00 in a café in Leith; membership £20 a year, £10 for students. Drupal CMS site: a Canvas page *How to join* (`/join`: Heading, Grid 67%-33% with Text and an Icon card), and a Utility page *Summer barbecue* in the Trash. |

## Sources

- The author's **Drupal in a Day** manuscript (Google Doc
  `14CE3MZ9SqTBhkkF6rZ-JzUpsl6J-5PLqC6UaPiaq95U`): the order of topics and many of the examples
  come from it. Its thread: a page → content types → layouts and view modes → media → image styles
  → modules, recipes, Composer → a new content type → taxonomy → Views → blocks → users → themes →
  Pathauto → multilingual → security updates.
- The companion book, `websites/ru/book-rewrite`: the build tooling and the chapter workflow come
  from there.

## Open items

- `archive/developer-qa/`: the author chose the module book's backlog (2026-11-04). The entry is in
  `websites/ru/book-rewrite/PROJECT-LOG.md` ("Topics to place"), uncommitted there. Delete the archive here once
  that book has taken the drafts.
- Chapter 2: the author's own story, in "Who makes Drupal?" (a `%%` placeholder). Deferred by the author on
  2026-11-04.
- **The Standard profile changed in Drupal 11.4**: no Article and Page, comments off, Navigation on (see "Article and Page" under Decisions for the plan). Chapter 7's draft uses Basic page from Drupal CMS, with Drupal CMS screenshots: on core, Basic page now comes from Chapter 6, so retake them. Decided: built by hand in Chapter 6 (see "Article and Page" under Decisions).
- Chapter 3: the author's own memories (which version they started on, the move from 7 to 8), a `%%` placeholder at the end of the Drupal 8 section.
- Two screenshots no chapter uses yet: `07-content-type-listing-of-a-newly-installed-drupal-site.png`
  and `08-media-content-list.png`.
- `tools/screenshots.py` has Chapter 6's screenshots. Add Chapter 4's and 5's (taken from scripts outside the repository). The sites have moved on since then (Chapter 6's pages and menu exist), so screenshots of earlier chapters either accept that, or need a fresh site in that chapter's state. Chapter 5's need a hover over the Site branding block for the pencil menu.
- Chapter 6, the Canvas screenshots: Mercury on the Starter template has no padding, so *How to join* looks cramped (Figure 6.11), and the editor's preview is partly hidden behind the panels (Figure 6.10). Retake them by hand if the author prefers, or once Canvas runs on the core site.
- Chapter 4, not tested: `ddev drush site:install` on Drupal 12 (and its drop-tables question), and Exercise 4's `ddev delete`.
- `slides/` and `tools/slides.py`: start with the first reviewed chapter.

## Backlog

Ideas that have no chapter yet, or are waiting for one.

- **Build your own Canvas component** (advanced; partly theming). Maybe the end of Chapter 14, or
  an appendix.
- **Revisit Chapter 4 when Drupal 12.0.0 is released** (planned for the week of 7 December 2026): the installer was written against 12.0.0-beta2 (no profile step; Standard is chosen for you), so walk through it again, retake the screenshots, and drop the `@beta` note.
- **Mercury instead of Olivero** in Chapter 4, once Mercury has a stable Drupal 12 release (1.0.5 requires ^11.3, 2026-11-04). It's Drupal CMS's front-end theme, so core and Drupal CMS readers would see the same site.
- **Drush for Drupal 12**: check before publication that a stable Drush release supports Drupal 12, and that `ddev composer require drush/drush` installs it without dev stability.
- **Lando** installation (Chapter 4 points to Appendix A).
- **Drupal Forge and the Drupal CMS Launcher** as no-install ways to try Drupal (in the Drupal in a
  Day manuscript).
- **Stage File Proxy** and working with a copy of a live site (Drupal in a Day "Final words").
- **Password Policy** module, shown in Drupal in a Day next to User 1.
- **Module Filter** as the first module installed through Project Browser (Drupal in a Day).
- **Photos for the club site**: where to find openly licensed photos (Wikimedia Commons, Openverse; check
  the license is compatible with CC BY-SA 4.0, and credit the photographer), and Devel Generate (the Devel
  module's submodule) to fill the site with test content and placeholder images. Probably Chapter 8 (finding
  photos, credits as a field) and Chapter 10 (Devel as a module you install with Composer, for development only).
  Ask the author whether they want to contribute their own photos.
- **"Coming from WordPress?" boxes** (the author, 2026-11-04), one each where it matters, as a comparison and
  never a contest: Chapter 6, the block editor vs. Canvas and Layout Builder (done); Chapter 7, custom post types and ACF
  vs. content types and fields; Chapter 10, plugins vs. modules, and installing from the dashboard vs. Composer
  (and Project Browser); Chapter 12, widgets vs. blocks, and the two meanings of "block"; Chapter 13, the six
  predefined roles vs. Drupal's own roles. Check each WordPress claim against wordpress.org when writing it.
- **How this book was written, and how it's kept up to date** (the author, 2026-11-05). Probably a section in the Preface. Say openly that AI (Claude) assists, mostly with maintenance, and that the layout, the structure and the text were decided by people first. Explain what the build makes possible: `tools/build.py`, includes and `{{ number:... }}` placeholders let us replace parts of the book (a retaken screenshot when an example's screen changes, a version number, a support date) without rewriting it. Also how the book covers two versions at once (Drupal 11.5 and 12 now, core and Drupal CMS), and how it moves to one when a major release is stable (around 12.1): what gets dropped, what gets rewritten, and who checks it. Useful for future maintainers as much as for readers.
- ~~**Trash**~~: in Chapter 6 (an "On Drupal CMS" box).
- **Diff** (compare revisions side by side): mentioned in Chapter 6 as a module for Chapter 10.
- A Drupal Association plug, and connecting Drupal skills to jobs (empty sections at the end of
  the Drupal in a Day manuscript).
