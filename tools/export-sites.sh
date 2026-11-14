#!/usr/bin/env bash
# Export the book's test sites into sites/, so they can be rebuilt anywhere.
#
# Usage: tools/export-sites.sh [core|cms]     (both when no argument)
#
#   ~/websites/open-university/lens-and-trail      -> sites/core/
#   ~/websites/open-university/lens-and-trail-cms  -> sites/cms/
#
# Each sites/<name>/ gets:
#
#   codebase/        composer.json, composer.lock and patches: `composer install`
#                    gives the same code. Also DDEV's config.yaml (PHP version etc.).
#   config/          the full configuration export. Installed on a new site with
#                    `drush site:install --existing-config`.
#   files/           files the configuration points to that aren't file
#                    entities (a theme's uploaded logo). Copied into the
#                    rebuilt site's sites/default/files/.
#   after-import.php run on the rebuilt site after the content recipe: puts
#                    back what the import can't bring (Focal Point's crops,
#                    from focal-points.json).
#   content/         a recipe holding the site's content, from core's
#                    content:export (nodes, terms, media and their files, blocks,
#                    menu links, users, comments...). Applied with `drush recipe`.
#
# The companion book, Theming Drupal, builds its test sites from these
# folders (its tools/setup.sh), so a change made here can be rebuilt there.
# Run this after a chapter changes a site, then commit sites/ with the chapter.
#
# Left out on purpose:
#   - user 0 (anonymous) and user 1 (admin): every new install makes its own.
#     Exported content refers to user 1 by ID, so it's admin on the new site too.
#   - path aliases of content: they come with their content (the path field);
#     only aliases that belong to no entity are exported (tools/export-content.php).
#   - content_moderation_state: comes with its content (moderation_state).
#   - easy_email: Drupal CMS's log of sent emails.
#   - crop: Focal Point makes the crops when the images are imported, from the
#     focal point exported with each image (tools/export-content.php).
#   - key.key.*: API keys (AI providers, Chapter 19). Even encrypted, they don't
#     belong in a public repository; enter your own on a rebuilt site.
set -euo pipefail

cd "$(dirname "$0")/.."
REPO=$(pwd)
BASE=${BASE:-$HOME/websites/open-university}

CONTENT_TYPES=(user taxonomy_term file media node block_content menu_link_content comment redirect canvas_page path_alias)

export_site() {
  local name=$1 site=$2
  local site_dir=$BASE/$site out=$REPO/sites/$name
  if [[ ! -d "$site_dir/.ddev" ]]; then
    echo "No DDEV project at $site_dir" >&2
    exit 1
  fi
  echo "== $site -> sites/$name"
  local tmp=.export-tmp
  rm -rf "${site_dir:?}/$tmp"

  # The codebase.
  rm -rf "$out/codebase"
  mkdir -p "$out/codebase/.ddev"
  cp "$site_dir/composer.json" "$site_dir/composer.lock" "$out/codebase/"
  [[ -d "$site_dir/patches" ]] && cp -R "$site_dir/patches" "$out/codebase/"
  [[ -f "$site_dir/patches.lock.json" ]] && cp "$site_dir/patches.lock.json" "$out/codebase/"
  cp "$site_dir/.ddev/config.yaml" "$out/codebase/.ddev/config.yaml"

  (
    cd "$site_dir"
    # Configuration.
    mkdir -p "$tmp"
    ddev drush config:export -y --destination="/var/www/html/$tmp/config" >/dev/null
    # Content: every content entity type in CONTENT_TYPES that exists on this
    # site, into a recipe's content/ folder, keeping IDs and dates (see
    # tools/export-content.php). The script is copied into the site, because
    # DDEV's container only sees the site's own folder.
    cp "$REPO/tools/export-content.php" "$tmp/"
    ddev drush php:script "$tmp/export-content.php" -- "/var/www/html/$tmp/content" "${CONTENT_TYPES[@]}" 2>&1 \
      | grep -v -e '^$' -e 'referenced by Term Parents'
  )

  rm -rf "$out/config" "$out/content" "$out/after-import.php"
  mkdir -p "$out/content"
  rsync -a "$site_dir/$tmp/config/" "$out/config/"
  rm -f "$out"/config/key.key.*.yml
  # Search API servers on the AI Search backend (Chapter 23), and their
  # indexes, go out disabled: without the keys, saving a hike makes the index
  # call the vector database, and the content import stops with a fatal error.
  # Enter your own keys on the rebuilt site, then switch them on.
  for server in "$out"/config/search_api.server.*.yml; do
    [[ -f "$server" ]] && grep -q "^backend: search_api_ai_search$" "$server" || continue
    local id
    id=$(basename "$server" .yml); id=${id#search_api.server.}
    perl -pi -e 's/^status: true$/status: false/' "$server"
    grep -l "^server: $id$" "$out"/config/search_api.index.*.yml | while read -r index; do
      perl -pi -e 's/^status: true$/status: false/' "$index"
    done
  done
  rsync -a "$site_dir/$tmp/content/" "$out/content/content/"
  rm -f "$out/focal-points.json"
  [[ -f "$site_dir/$tmp/focal-points.json" ]] && cp "$site_dir/$tmp/focal-points.json" "$out/"
  cp "$REPO/tools/after-import.php" "$out/"
  # core's exporter saves each file under its file name (photo.jpg), but the
  # importer looks for it under its URI's name (photo_1.jpg, when Drupal had to
  # rename a second upload). Copy each file again under the URI's name.
  if [[ -d "$out/content/content/file" ]]; then
    rm -f "$out"/content/content/file/*.{jpg,jpeg,png,gif,webp,avif,svg,pdf}
    for file in "$out"/content/content/file/*.yml; do
      uri=$("$REPO/.venv/bin/python" -c "import sys, yaml; print(yaml.safe_load(open(sys.argv[1]))['default']['uri'][0]['value'])" "$file")
      cp "$site_dir/web/sites/default/files/${uri#public://}" "$out/content/content/file/$(basename "$uri")"
    done
  fi
  rm -rf "${site_dir:?}/$tmp"

  # Users 0 and 1: find them by their name (empty, and the site's admin).
  for file in "$out"/content/content/user/*.yml; do
    if "$REPO/.venv/bin/python" - "$file" <<'PY'
import sys, yaml
data = yaml.safe_load(open(sys.argv[1]))
name = (data.get("default", {}).get("name") or [{"value": ""}])[0]["value"]
sys.exit(0 if name in ("", "admin") or name.startswith("admin@") else 1)
PY
    then
      rm "$file"
    fi
  done

  # Files the configuration points to that aren't file entities, such as a
  # theme's uploaded logo (theme settings store public://...). They go in
  # files/, to copy into the rebuilt site's public files folder.
  rm -rf "$out/files"
  grep -rhoE "public://[^'\" ]+" "$out/config" | sort -u | while read -r uri; do
    local path=${uri#public://}
    if [[ -f "$site_dir/web/sites/default/files/$path" ]]; then
      mkdir -p "$out/files/$(dirname "$path")"
      cp "$site_dir/web/sites/default/files/$path" "$out/files/$path"
    fi
  done

  cat > "$out/content/recipe.yml" <<RECIPE
name: 'Lens & Trail content ($name site)'
description: 'The content of the photo club site at the end of the site-building book. Made by tools/export-sites.sh; do not edit by hand.'
type: Site
RECIPE

  echo "   config: $(find "$out/config" -name '*.yml' | wc -l | tr -d ' ') files"
  echo "   content: $(find "$out/content/content" -name '*.yml' | wc -l | tr -d ' ') entities"
}

case "${1:-both}" in
  core) export_site core lens-and-trail ;;
  cms) export_site cms lens-and-trail-cms ;;
  both)
    export_site core lens-and-trail
    export_site cms lens-and-trail-cms
    ;;
  *) echo "Usage: tools/export-sites.sh [core|cms]" >&2; exit 1 ;;
esac
