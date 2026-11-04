# Project log

Decisions, history, and open items for the book. `README.md` has the layout, the commands, and
the chapter status. Keep both up to date at the end of every chapter.

Last updated: 2026-11-04.

## How we work

- **The author** (Hilmar Kári Hallbjörnsson) decides what goes in, reviews every chapter, and
  pushes and merges. Claude drafts, builds, and commits.
- **One chapter at a time.** Before drafting a chapter, Claude asks the author questions about what
  to include and leave out ("grilling"). The author reviews the draft before the next chapter starts.
- **Branches**: one branch per unit of work, created only after the author says yes in the
  conversation. Claude never commits to `main`, pushes, opens pull requests, or merges.
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
| Theme file structure | Moved from Chapter 1 to Chapter 14 (`manuscript/14-appearance.md`), where it'll be reworked. |

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
  configuration vs. content, summary, five exercises, and verified links. Awaiting the author's review.

## The photo club site

What each chapter adds to the Lens & Trail site. Later chapters and exercises must not contradict it.

| Chapter | Adds |
|---|---|
| 1 | Introduces the club and what its site needs: hikes, photos, galleries, members, news, pages, categories (places, photo themes), English and Spanish; roles: visitor, member, hike leader, secretary, administrator. Exercise 4 (who does what) is reused in Chapter 13; Exercise 5 (model a hike) is compared with Chapter 7. |

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
- Two screenshots no chapter uses yet: `07-content-type-listing-of-a-newly-installed-drupal-site.png`
  and `08-media-content-list.png`.
- The test sites and `tools/screenshots.sh`: set up with Chapter 4, so screenshots can be retaken
  whenever Drupal CMS changes. Two DDEV sites are needed, one Drupal core and one Drupal CMS.
- `slides/` and `tools/slides.py`: start with the first reviewed chapter.

## Backlog

Ideas that have no chapter yet, or are waiting for one.

- **Build your own Canvas component** (advanced; partly theming). Maybe the end of Chapter 14, or
  an appendix.
- **Lando** installation (Chapter 4 says "TBA").
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
- **Trash** (deleted content can be restored in Drupal CMS).
- A Drupal Association plug, and connecting Drupal skills to jobs (empty sections at the end of
  the Drupal in a Day manuscript).
