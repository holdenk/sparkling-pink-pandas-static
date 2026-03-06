#!/usr/bin/env python3
"""
Fix gallery dates using Google Photos Takeout JSON sidecar files.

Google Photos Takeout exports each photo alongside a .json metadata file
containing the original photo-taken timestamp. This script matches gallery
images to their Takeout JSON sidecars and backfills missing dates in
_data/gallery.yml.

Usage:
    python3 scripts/fix_gallery_dates.py TAKEOUT_DIR [--dry-run]

Arguments:
    TAKEOUT_DIR    Path to the Google Photos Takeout directory (e.g.,
                   ~/google_photos_takeout). This directory typically
                   contains album subdirectories, each with photos and
                   their .json sidecar files.

Options:
    --dry-run      Show what dates would be updated without writing changes.

Requires: pip install pyyaml
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

from utils import GALLERY_WEB_PREFIX, insert_gallery_dates, load_gallery_yaml


def find_json_sidecars(takeout_dir):
    """Walk the takeout directory and build a map of photo filename -> JSON path.

    Google Takeout names the sidecar as <photo_filename>.json.
    Handles several known quirks:
      - Standard: IMG_1234.jpg -> IMG_1234.jpg.json
      - Truncated: long filenames get base name cut to 46 chars
      - Duplicate counter: IMG_1234(1).jpg -> IMG_1234.jpg(1).json
    """
    sidecar_map = {}

    for dirpath, _dirnames, filenames in os.walk(takeout_dir):
        json_files = [f for f in filenames if f.endswith('.json') and f != 'metadata.json']

        for jf in json_files:
            json_path = os.path.join(dirpath, jf)

            # Derive the photo filename this JSON belongs to.
            # Standard case: strip trailing .json to get the photo filename.
            photo_name = jf[:-5]  # remove .json

            # Handle duplicate counter quirk: IMG_1234.jpg(1) -> IMG_1234(1).jpg
            counter_match = re.match(r'^(.+?)(\.[^.]+)(\(\d+\))$', photo_name)
            if counter_match:
                # Reorder: base + counter + ext
                photo_name_alt = counter_match.group(1) + counter_match.group(3) + counter_match.group(2)
                sidecar_map[photo_name_alt.lower()] = json_path

            sidecar_map[photo_name.lower()] = json_path

    return sidecar_map


def parse_takeout_date(json_path):
    """Extract the photo-taken date from a Takeout JSON sidecar.

    Returns a datetime.date or None.

    The JSON structure has a photoTakenTime field:
        {
            "photoTakenTime": {
                "timestamp": "1681567436",
                "formatted": "Apr 15, 2023, 2:23:56 PM UTC"
            }
        }

    The timestamp is a Unix epoch in seconds, stored as a string.
    A value of "0" means the date is unknown.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    photo_taken = data.get('photoTakenTime', {})
    ts_str = photo_taken.get('timestamp', '0')

    if not ts_str or ts_str == '0':
        return None

    try:
        ts = int(ts_str)
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.date()
    except (ValueError, OSError):
        return None




def main():
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0)

    takeout_dir = os.path.expanduser(sys.argv[1])
    dry_run = '--dry-run' in sys.argv

    if not os.path.isdir(takeout_dir):
        print(f"Takeout directory not found: {takeout_dir}")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    gallery_yml = os.path.join(repo_root, '_data', 'gallery.yml')

    web_prefix = GALLERY_WEB_PREFIX

    entries = load_gallery_yaml(gallery_yml)
    if not entries:
        print(f"Gallery file not found or empty: {gallery_yml}")
        sys.exit(1)

    # Find entries missing dates
    missing_dates = []
    for entry in entries:
        if not entry or entry.get('date') or not entry.get('image'):
            continue
        image_path = entry['image']
        if not image_path.startswith(web_prefix):
            continue
        filename = image_path[len(web_prefix):]
        missing_dates.append((entry, filename))

    if not missing_dates:
        print("All gallery entries already have dates. Nothing to do.")
        return

    print(f"Found {len(missing_dates)} gallery entries missing dates.")
    print(f"Scanning takeout directory: {takeout_dir}")

    sidecar_map = find_json_sidecars(takeout_dir)
    print(f"Found {len(sidecar_map)} JSON sidecar files.\n")

    # Match and extract dates
    updated = []
    not_found = []
    no_date = []

    for entry, filename in missing_dates:
        key = filename.lower()

        # Try exact match first
        json_path = sidecar_map.get(key)

        # Try without extension variations
        if not json_path:
            base, ext = os.path.splitext(key)
            # Try truncated name (46 char limit on base)
            if len(base) > 46:
                truncated_key = base[:46] + ext
                json_path = sidecar_map.get(truncated_key)

        if not json_path:
            not_found.append(filename)
            continue

        date = parse_takeout_date(json_path)
        if not date:
            no_date.append(filename)
            continue

        updated.append((entry, date, filename))

    # Report results
    prefix = "[dry-run] " if dry_run else ""

    if updated:
        print(f"{prefix}Updating dates for {len(updated)} entries:\n")
        for _, date, filename in updated:
            print(f"  {prefix}{filename} -> {date.isoformat()}")

    if not_found:
        print(f"\nNo matching JSON sidecar found for {len(not_found)} files:")
        for fn in not_found[:10]:
            print(f"  {fn}")
        if len(not_found) > 10:
            print(f"  ... and {len(not_found) - 10} more")

    if no_date:
        print(f"\nJSON found but no date available for {len(no_date)} files:")
        for fn in no_date[:10]:
            print(f"  {fn}")
        if len(no_date) > 10:
            print(f"  ... and {len(no_date) - 10} more")

    if dry_run:
        print("\nDry run complete. Use without --dry-run to apply changes.")
        return

    if not updated:
        print("\nNo dates to update.")
        return

    # Write changes by modifying the YAML file
    insert_gallery_dates(gallery_yml, [(entry, dt) for entry, dt, _ in updated])

    print(f"\nDone. Updated {len(updated)} dates in gallery.yml.")


if __name__ == '__main__':
    main()
