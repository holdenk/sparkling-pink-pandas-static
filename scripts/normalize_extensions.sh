#!/usr/bin/env bash
#
# Normalize gallery image extensions to lowercase.
#
# Renames .JPG → .jpg, .JPEG → .jpeg, .PNG → .png in assets/img/gallery/.
# When a lowercase file already exists (duplicate), keeps the lowercase
# version and removes the uppercase one plus its gallery.yml entry.
# Updates _data/gallery.yml references to match.
#
# Usage:
#     bash scripts/normalize_extensions.sh [--dry-run]
#
# Options:
#     --dry-run   Show what would change without modifying any files.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GALLERY_DIR="$REPO_ROOT/assets/img/gallery"
GALLERY_YML="$REPO_ROOT/_data/gallery.yml"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

renamed=0
deleted=0

echo "Scanning $GALLERY_DIR for uppercase extensions..."
echo ""

for upper_file in "$GALLERY_DIR"/*.JPG "$GALLERY_DIR"/*.JPEG "$GALLERY_DIR"/*.PNG; do
    [[ -f "$upper_file" ]] || continue

    filename="$(basename "$upper_file")"
    base="${filename%.*}"
    ext="${filename##*.}"
    lower_ext="$(echo "$ext" | tr '[:upper:]' '[:lower:]')"
    lower_file="$GALLERY_DIR/${base}.${lower_ext}"

    if [[ -f "$lower_file" ]]; then
        # Duplicate: both cases exist — keep lowercase, remove uppercase
        echo "DUPLICATE: $filename (keeping ${base}.${lower_ext}, removing $filename)"
        if [[ "$DRY_RUN" == false ]]; then
            rm "$upper_file"
            # Remove the uppercase entry line and any immediately following metadata
            # lines (indented with spaces) from gallery.yml
            sed -i "/- image: \/assets\/img\/gallery\/${filename}$/d" "$GALLERY_YML"
        fi
        ((deleted++)) || true
    else
        echo "RENAME:    $filename -> ${base}.${lower_ext}"
        if [[ "$DRY_RUN" == false ]]; then
            mv "$upper_file" "$lower_file"
        fi
        ((renamed++)) || true
    fi
done

# Update remaining uppercase references in gallery.yml
if [[ "$DRY_RUN" == false ]]; then
    sed -i 's/\.JPG/.jpg/g; s/\.JPEG/.jpeg/g; s/\.PNG/.png/g' "$GALLERY_YML"
fi

echo ""
echo "Renamed: $renamed"
echo "Deleted duplicates: $deleted"

if [[ "$DRY_RUN" == true ]]; then
    echo ""
    echo "(dry run — no files were changed)"
fi
