#!/usr/bin/env python3
"""Fetches the current numbers from their sources, and updates data/numbers.yml.

The book uses them as {{ number:name }}; tools/build.py fills them in.

Every entry in data/numbers.yml with a fetch: section is looked up at its
source. The script prints a table of what changed, and writes the new values
(and today's date as checked:) into the file, keeping its comments and order.
Entries without fetch: are listed at the end, to check by hand.

Usage:
  python3 tools/update_numbers.py                     fetch and update
  python3 tools/update_numbers.py --dry-run           fetch and report only
  python3 tools/update_numbers.py drupal_version      only these entries

Needs PyYAML (python3 -m pip install -r requirements.txt).

Set GITHUB_TOKEN if GitHub's limit of 60 requests an hour gets in the way.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NUMBERS = ROOT / "data" / "numbers.yml"
AGENT = "Mozilla/5.0 (Drupal site-building book number updater)"
STABLE = re.compile(r"^v?\d+(\.\d+)*$")


class FetchError(Exception):
    pass


def get(url: str) -> str:
    headers = {"User-Agent": AGENT}
    if "api.github.com" in url and os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except Exception as error:
        raise FetchError(f"{url}: {error}") from None


def get_json(url: str):
    text = get(url)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise FetchError(f"{url}: not JSON") from None


def walk(data, path: str):
    """Follows a dotted path: keys, list indexes, * (every item), [key=value]."""
    items = [data]
    for part in path.split("."):
        found = []
        for item in items:
            if part == "*":
                found += list(item) if isinstance(item, list) else []
            elif part.startswith("[") and part.endswith("]"):
                key, _, value = part[1:-1].partition("=")
                match = next((x for x in item if isinstance(x, dict) and str(x.get(key)) == value), None)
                if match is not None:
                    found.append(match)
            elif isinstance(item, list) and part.isdigit() and int(part) < len(item):
                found.append(item[int(part)])
            elif isinstance(item, dict) and part in item:
                found.append(item[part])
        if not found:
            raise FetchError(f"nothing at '{part}' in path {path}")
        items = found
    return [str(x) for x in items]


def w3techs(slug: str, share: str) -> list[str]:
    html = get(f"https://w3techs.com/technologies/details/{slug}")
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html))
    cms = re.search(r"is used by (less than 0\.1%|\d+(?:\.\d+)?%) of all the websites whose content management system", text)
    if not cms:
        raise FetchError(f"W3Techs {slug}: no usage sentence (has the page changed?)")
    if share == "cms":
        return ["< 0.1%" if cms.group(1).startswith("less") else cms.group(1)]
    everything = re.search(r"This is (\d+(?:\.\d+)?%) of all websites", text)
    if everything:
        return [everything.group(1)]
    if cms.group(1).startswith("less"):
        return ["< 0.1%"]
    raise FetchError(f"W3Techs {slug}: no share of all websites")


def version_key(value: str):
    return [int(x) if x.isdigit() else x for x in re.split(r"[.\-]", value.lstrip("v"))]


def fetch(spec: dict) -> str:
    if "json" in spec:
        values = walk(get_json(spec["json"]), spec["path"])
    elif "text" in spec:
        values = re.findall(spec["regex"], get(spec["text"]), re.S | re.M)
    elif "npm" in spec:
        values = [get_json(f"https://registry.npmjs.org/{spec['npm']}/latest")["version"]]
    elif "pypi" in spec:
        values = [get_json(f"https://pypi.org/pypi/{spec['pypi']}/json")["info"]["version"]]
    elif "nuget" in spec:
        values = get_json(f"https://api.nuget.org/v3-flatcontainer/{spec['nuget'].lower()}/index.json")["versions"]
    elif "github_release" in spec:
        values = [get_json(f"https://api.github.com/repos/{spec['github_release']}/releases/latest")["tag_name"]]
    elif "github_tags" in spec:
        values = [tag["name"] for tag in get_json(f"https://api.github.com/repos/{spec['github_tags']}/tags?per_page=100")]
    elif "w3techs" in spec:
        values = w3techs(spec["w3techs"], spec.get("share", "all"))
    else:
        raise FetchError(f"unknown fetch method in {spec}")

    if "regex" in spec and "text" not in spec:
        values = [m for v in values for m in re.findall(spec["regex"], v)]
    if spec.get("stable"):
        values = [v for v in values if STABLE.match(v)]
    if not values:
        raise FetchError("no value found")
    value = max(values, key=version_key) if spec.get("pick") == "max" else values[0]
    value = value.lstrip("v") if STABLE.match(value) else value
    if "add" in spec:
        value = str(int(value) + int(spec["add"]))
    if spec.get("format") == "thousands":
        value = f"{int(value):,}"
    return value


def set_value(text: str, key: str, value: str) -> str:
    block = re.compile(rf"(^  {re.escape(key)}:\n(?:(?:    .*)?\n)*?    value: )'[^']*'", re.M)
    new, count = block.subn(lambda m: m.group(1) + "'" + value.replace("'", "''") + "'", text, count=1)
    if count != 1:
        raise SystemExit(f"Could not find value: for {key} in {NUMBERS.name}")
    return new


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    data = yaml.safe_load(NUMBERS.read_text())
    entries = data["numbers"]
    unknown = [a for a in args if a not in entries]
    if unknown:
        print(f"Unknown entries: {', '.join(unknown)}", file=sys.stderr)
        return 2

    text = NUMBERS.read_text()
    changed, failed, manual = [], [], []
    for key, entry in entries.items():
        if args and key not in args:
            continue
        if "fetch" not in entry:
            manual.append((key, entry))
            continue
        try:
            value = fetch(entry["fetch"])
        except (FetchError, KeyError, IndexError, ValueError) as error:
            failed.append((key, str(error)))
            print(f"  ?  {key:20} {error}")
            continue
        old = str(entry["value"])
        if value != old:
            changed.append(key)
            text = set_value(text, key, value)
            print(f"  *  {key:20} {old} -> {value}")
        else:
            print(f"     {key:20} {old}")

    if manual:
        print("\nCheck by hand:")
        for key, entry in manual:
            print(f"     {key:20} {entry['value']!s:20} {entry['source']}")
    if failed:
        print(f"\n{len(failed)} could not be fetched; their values are unchanged. Check them by hand.")

    if dry_run:
        print(f"\n{len(changed)} changed (dry run, nothing written).")
        return 0
    text = re.sub(r"^checked: '[^']*'", f"checked: '{datetime.date.today().isoformat()}'", text, count=1, flags=re.M)
    NUMBERS.write_text(text)
    print(f"\n{len(changed)} changed. Wrote {NUMBERS.relative_to(ROOT)}; now run tools/build.py.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
