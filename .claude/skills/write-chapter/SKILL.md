---
name: write-chapter
description: Use when drafting, rewriting, or revising a chapter or appendix of the Drupal site-building book in this project (manuscript/, book/, slides/). Covers asking the author about scope first, the author's voice, the photo club running example, showing both Drupal core and Drupal CMS, chapter structure with exercises, screenshots, building, and finishing a chapter.
---

# Writing a chapter

The book teaches site building to people who have never seen Drupal. Read `README.md` and
`PROJECT-LOG.md` (decisions, backlog) before starting.

## 1. Ask first

Before drafting, ask the author a short round of questions ("grill" them): what to include, what
to leave out, which examples from the Drupal in a Day manuscript to keep, where backlog items fit,
and anything you'd otherwise have to guess. Recommend an answer for each. Don't draft until they've
answered; for the questions they skip, use your recommendation and say so in the report.

## 2. Gather the material

- The existing draft in `manuscript/NN-*.md`: keep the author's text, examples and jokes where they
  work; rewrite where it's dense or abstract.
- The Drupal in a Day manuscript (Google Doc in `PROJECT-LOG.md` "Sources"): the order of topics and
  the live examples. Its "why is this page empty? → Views" hand-offs between topics are worth
  keeping.
- Check facts against current Drupal core and Drupal CMS (drupal.org documentation, change records,
  the actual interface). Prefer what you see in a running site over memory. Record anything
  release-dependent in the README's "Check before publication".

## 3. Voice

Match the author's own chapters (the best examples: Chapter 1, the history, the installation).

- Conversational and warm. "We" for the authors' experience ("we've been teaching Drupal for a long
  time") and for doing things together, "you" for the reader. Never "I": the book will have more
  than one author (the author's decision, 2026-11-06). The exceptions: a personal story, signed with the
  author's name (Hilmar's story in Chapter 2), and a fact about one person, which names them ("When Hilmar
  installed it, it said Reykjavik"). The reader's own questions ("Which one should I use?") stay as they are.
- Reassure where it's hard: "don't worry", "it takes a while to wrap your head around this".
  Admit when there's no clean answer ("sometimes we have to follow our guts").
- **Introduce every new tool, module or product properly** (the author's rule, 2026-11-12): when something new comes in (SDC Styleguide, Storybook, a contributed module, an outside service), give it a paragraph or two before using it: what it is, where it lives, what it does for the club's sites, and why we picked it over the alternatives. Never brush it off in a clause ("So we tried X, a module with no build step:") and go straight to the install command. The same goes for alternatives we turn down: say what they are before saying why not.
- Light humor is welcome, and so are the author's emoticons (`;-)`, `:-)`): they make the tone personal.
- Deeper than the slides: explain *why* every setting exists and what happens if you change it,
  not only where to click. Every new term is explained the first time it appears, in plain words,
  before any technical name ("bundle", "entity") is introduced.
- Point to other chapters in full, friendly sentences ("We also cover fields in Chapter 7."), never a bare
  "Chapter 7." tacked on the end of a paragraph (the author's review of Chapter 1).
- Never talk down: avoid "simply", "obviously", "easy", "of course", "just" (as in "just do X").
  Tone check before finishing:
  `grep -niE "\b(simply|obviously|easy|easily|of course|clearly|trivial|basically)\b" manuscript/NN-*.md`
- US spelling.

## 4. Structure of a chapter

1. A short opening: what this chapter covers and why it matters for the photo club site.
2. Sections in the order the reader would do things. Hands-on steps as numbered lists with the
   exact labels in **bold** (as they appear on screen). Paths in `code`, such as
   `/admin/structure/types`.
3. "Try it" blocks for the photo club site: `> **Try it:** ...`.
4. Where core and Drupal CMS differ, show both in boxes:
   `> **On Drupal core:** ...` and `> **On Drupal CMS:** ...`. Lean slightly towards core: explain
   the underlying mechanism, then show what Drupal CMS adds on top.
5. WordPress: add a `> **Coming from WordPress?**` box only where WordPress knowledge would mislead or genuinely
   help (the backlog lists where). It's a comparison, never a contest: "if you know this, here's the Drupal word
   for it". Check WordPress claims against wordpress.org.
6. Where page layout comes up, teach both Canvas and Layout Builder (with field-based displays) as
   equal approaches.
7. **Summary**: a short list of what the reader can now do.
8. **Exercises**: 3–6 per chapter, from repeating a step on new data to a small open task on the photo
   club site. Mark harder ones "(challenge)". Exercises must be doable with what the book has
   covered so far. An exercise that goes a step beyond its chapter is "(advanced)", ends with
   "(The answer is in Appendix C.)", and gets a tested answer, with the reasons, in
   `manuscript/appendix-c-answers-to-the-advanced-exercises.md`: the author doesn't want readers
   left hanging.
9. **Want to know more?**: links to drupal.org documentation and other free resources. Verify every
   link.

## 5. The running example

One site across the whole book: **Lens & Trail**, a small photography and hiking club in Edinburgh, in English
and Spanish, built on Drupal core with the Default Admin theme (built from Gin). Each chapter
starts from the state the previous chapter left it in, and says so in its opening. Keep a list of
what each chapter adds to the site in `PROJECT-LOG.md` ("The photo club site"), so later chapters
and exercises don't contradict it.

## 6. Screenshots and files

- **More screenshots rather than fewer.** This is a book for beginners: when in doubt, add the screenshot. The
  first time the reader does something with several steps (adding a field, building a layout), show a
  screenshot after each step, placed right after the step it shows, so they can check they're on the right
  screen. Later repeats of the same task can do with fewer. The book will most likely be a PDF, not
  printed, so space isn't a reason to leave a screenshot out. (The author, 2026-11-05.)
- Images in `manuscript/images/NN-what.png`, placed as
  `![What the image shows](images/NN-what.png)` then `*Figure N.M: Caption*` on its own line,
  numbered in order. No square brackets in alt text, no Obsidian `![[...]]` links.
- Once `tools/screenshots.sh` exists, add the chapter's screenshots to it so they can be retaken
  when Drupal changes. Ask the author for screenshots the script can't take.
- Files the reader sees (recipes, configuration, `composer.json` excerpts) go in `examples/` and are
  pulled in with `<!-- include: ... -->`. Short commands may be inline.
- Notes for the author: `%% ... %%` (stripped from `book/`).
- Numbers that go out of date (current versions, support dates, counts) aren't typed in: add them to
  `data/numbers.yml` with a source and a `fetch:` where possible, and write `{{ number:name }}`. Fixed
  history (a release date in the past) is plain text.
- One line per paragraph (and per list item): no hard-wrapped prose. Obsidian shows the line breaks.

## 7. Finish

- `python3 tools/build.py && python3 tools/build.py --check`.
- Update the README status row and "Check before publication", and `PROJECT-LOG.md` (history, the
  photo club site, open items, backlog).
- Teachers' kit: once `slides/` exists, add the chapter's deck and teaching notes (timings for a
  Drupal in a Day slot and a university lecture).
- Commit on the current branch (never `main`); ask before creating any branch.
- Report to the author: what was kept and what was rewritten from their draft, what is new, what was
  checked against a running site and what wasn't, every assumption, and the questions for their review.
