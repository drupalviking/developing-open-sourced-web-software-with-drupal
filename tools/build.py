#!/usr/bin/env python3
"""Builds the book's Markdown chapters from manuscript/ into book/.

The manuscript is written in Obsidian (or any Markdown editor). The build
turns it into plain Markdown that renders the same on GitHub, GitLab and
drupal.org, and that a later PDF/EPUB build can read.

What the build does:

  - Removes Obsidian comments, %% like this %%, on one line or several.
    Use them for notes to yourself and to other authors.
  - Fills in numbers that go out of date, {{ number:drupal_version }}, from
    data/numbers.yml (tools/update_numbers.py fetches the current ones).
    {{ number:checked }} is the date they were last fetched. An unknown name
    stops the build. Needs PyYAML: python3 -m pip install -r requirements.txt
  - Fails on Obsidian wiki links, ![[image.png]] or [[Page]]. Write
    ![Alt text](images/NN-name.png) instead (Obsidian does this for you when
    "Use [[Wikilinks]]" is off, which .obsidian/app.json sets).
  - Fails on an image link to a file that isn't in manuscript/images/.
  - Expands directives on a line of their own:

    <!-- include: examples/recipes/photo_club_gallery/recipe.yml -->
        The whole file, as a code block labeled with its path.
    <!-- include: <path> key=install -->
        One top-level YAML entry, with the comment lines directly above it.
        key=name,install gives several entries in one listing.
    <!-- include: <path> lines=12-20 -->
        Only these lines of the file.
    <!-- include: <path> as=recipes/photo_club/recipe.yml -->
        Label the listing with the path the reader sees.
    <!-- insert: manuscript/exercises/shared.md shift=1 -->
        Another Markdown file's content, with every heading shift=N levels
        lower.

    Directives inside a blockquote (> <!-- include: ... -->) are expanded
    inside it.

Usage:
  python3 tools/build.py           build book/ and remove files with no source
  python3 tools/build.py --check   fail if book/ is out of date (for CI)
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = ROOT / "manuscript"
BOOK = ROOT / "book"

LANGUAGES = {
    ".yml": "yaml",
    ".yaml": "yaml",
    ".json": "json",
    ".twig": "twig",
    ".sh": "bash",
    ".php": "php",
    ".twig": "twig",
    ".css": "css",
    ".txt": "text",
}

IMAGE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)\)")
WIKI_LINK = re.compile(r"!?\[\[[^\]]+\]\]")
COMMENT = re.compile(r"%%.*?%%", re.DOTALL)
NUMBER = re.compile(r"\{\{\s*number:([a-z0-9_]+)\s*\}\}")
NUMBERS_FILE = ROOT / "data" / "numbers.yml"
_numbers: dict[str, str] | None = None
DIRECTIVE = re.compile(r"^(?P<quote>(?:>\s?)*)<!--\s*(?P<kind>include|insert):\s*(?P<args>.+?)\s*-->$")


class BuildError(Exception):
    pass


def resolve(raw: str) -> Path:
    path = (ROOT / raw).resolve()
    if not path.is_file():
        raise BuildError(f"No such file: {raw}")
    return path


def dedent(lines: list[str]) -> list[str]:
    indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]
    cut = min(indents) if indents else 0
    return [line[cut:] if line.strip() else "" for line in lines]


def extract_yaml_key(lines: list[str], key: str, path: Path) -> list[str]:
    if "," in key:
        result: list[str] = []
        for one in key.split(","):
            result += extract_yaml_key(lines, one.strip(), path)
        return result
    for index, line in enumerate(lines):
        if line.rstrip() == f"{key}:" or line.startswith(f"{key}: "):
            start = index
            while start > 0 and lines[start - 1].startswith("#"):
                start -= 1
            end = index + 1
            while end < len(lines) and (lines[end].startswith(" ") or lines[end].strip() == ""):
                end += 1
            while lines[end - 1].strip() == "":
                end -= 1
            return lines[start:end]
    raise BuildError(f"No top-level key {key} in {path.name}")


def extract_lines(lines: list[str], value: str, path: Path) -> list[str]:
    match = re.fullmatch(r"(\d+)-(\d+)", value)
    if not match:
        raise BuildError(f"lines= needs a range such as 12-20, not '{value}'")
    first, last = int(match.group(1)), int(match.group(2))
    if not 1 <= first <= last <= len(lines):
        raise BuildError(f"lines={value} is outside {path.name}, which has {len(lines)} lines")
    return dedent(lines[first - 1:last])


def include(args: str) -> str:
    raw_path, *options = args.split()
    path = resolve(raw_path)
    lines = path.read_text().rstrip("\n").split("\n")
    label = path.relative_to(ROOT).as_posix()
    for option in options:
        kind, _, value = option.partition("=")
        if kind == "lines":
            lines = extract_lines(lines, value, path)
        elif kind == "key":
            lines = extract_yaml_key(lines, value, path)
        elif kind == "as":
            label = value
        else:
            raise BuildError(f"Unknown include option '{option}'")
    source = path.relative_to(ROOT).as_posix()
    body = "\n".join(lines)
    return f"`{label}` ([source](../{source}))\n\n```{LANGUAGES.get(path.suffix, '')}\n{body}\n```"


def insert(args: str) -> str:
    raw_path, *options = args.split()
    path = resolve(raw_path)
    shift = 0
    for option in options:
        kind, _, value = option.partition("=")
        if kind != "shift" or not value.isdigit():
            raise BuildError(f"Unknown insert option '{option}'")
        shift = int(value)
    lines = build(path).split("\n")
    in_code = False
    for index, line in enumerate(lines):
        if line.startswith("```"):
            in_code = not in_code
        elif not in_code and re.match(r"#{1,6} ", line):
            lines[index] = "#" * shift + line
    return "\n".join(lines).strip("\n")


def numbers() -> dict[str, str]:
    global _numbers
    if _numbers is None:
        try:
            import yaml
        except ImportError:
            raise BuildError("the manuscript uses {{ number:... }}, which needs PyYAML: python3 -m pip install -r requirements.txt") from None
        import datetime
        data = yaml.safe_load(NUMBERS_FILE.read_text())
        _numbers = {key: str(entry["value"]) for key, entry in data["numbers"].items()}
        checked = datetime.date.fromisoformat(str(data["checked"]))
        _numbers["checked"] = f"{checked.day} {checked:%B %Y}"
    return _numbers


def fill_numbers(text: str, source: Path) -> str:
    def replace(match: re.Match) -> str:
        values = numbers()
        if match.group(1) not in values:
            line = text.count("\n", 0, match.start()) + 1
            raise BuildError(f"{source.name}:{line}: unknown number {match.group(0)}; add it to data/numbers.yml")
        return values[match.group(1)]
    return NUMBER.sub(replace, text)


def build(source: Path) -> str:
    text = source.read_text()
    # Comments first, so a note may mention ![[a wiki link]] or a missing image.
    text = COMMENT.sub("", text)
    text = fill_numbers(text, source)
    output = []
    in_code = False
    for number, line in enumerate(text.split("\n"), start=1):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        if not in_code:
            if WIKI_LINK.search(line):
                raise BuildError(f"{source.name}:{number}: Obsidian wiki link {WIKI_LINK.search(line).group(0)}; use ![Alt text](images/NN-name.png)")
            for image in IMAGE.findall(line):
                if image.startswith(("http://", "https://")):
                    continue
                if not (source.parent / image).is_file():
                    raise BuildError(f"{source.name}:{number}: missing image {image}")
        match = DIRECTIVE.match(line.strip())
        if in_code or not match:
            output.append(line)
            continue
        try:
            kind, args = match.group("kind"), match.group("args")
            block = include(args) if kind == "include" else insert(args)
        except BuildError as error:
            raise BuildError(f"{source.name}:{number}: {error}") from None
        quote = "> " if match.group("quote") else ""
        output.append("\n".join((quote + part).rstrip() if part or quote else part for part in block.split("\n")))
    # Removing a comment can leave a run of blank lines behind.
    return re.sub(r"\n{3,}", "\n\n", "\n".join(output)).strip("\n") + "\n"


def copy_images(check: bool) -> list[str]:
    stale = []
    source_dir, target_dir = MANUSCRIPT / "images", BOOK / "images"
    if not source_dir.is_dir():
        return stale
    target_dir.mkdir(exist_ok=True)
    for source in sorted(source_dir.iterdir()):
        if not source.is_file() or source.name.startswith("."):
            continue
        target = target_dir / source.name
        if target.exists() and target.read_bytes() == source.read_bytes():
            continue
        if check:
            stale.append(f"images/{source.name}")
        else:
            shutil.copyfile(source, target)
            print(f"copied book/images/{source.name}")
    return stale


def write(source: Path, target: Path, check: bool) -> list[str]:
    content = build(source)
    name = target.relative_to(BOOK).as_posix()
    if check:
        return [] if target.exists() and target.read_text() == content else [name]
    if target.exists() and target.read_text() == content:
        return []
    target.parent.mkdir(exist_ok=True)
    target.write_text(content)
    print(f"built book/{name}")
    return []


def remove_orphans(check: bool) -> list[str]:
    expected = {
        BOOK: {source.name for source in MANUSCRIPT.glob("*.md")},
        BOOK / "images": {s.name for s in (MANUSCRIPT / "images").glob("*") if s.is_file() and not s.name.startswith(".")},
    }
    orphans = []
    for target_dir, names in expected.items():
        if not target_dir.is_dir():
            continue
        for target in sorted(target_dir.glob("*.md" if target_dir == BOOK else "*")):
            if not target.is_file() or target.name in names or target.name == "README.md":
                continue
            name = target.relative_to(BOOK).as_posix()
            if check:
                orphans.append(name)
            else:
                target.unlink()
                print(f"removed book/{name}")
    return orphans


def main() -> int:
    check = "--check" in sys.argv
    BOOK.mkdir(exist_ok=True)
    stale: list[str] = []
    try:
        for source in sorted(MANUSCRIPT.glob("*.md")):
            stale += write(source, BOOK / source.name, check)
        stale += copy_images(check)
        stale += remove_orphans(check)
    except BuildError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    if stale:
        print("out of date: " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
