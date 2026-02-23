#!/usr/bin/env python3
"""
Sync gallery photos: find images in assets/img/gallery/ that are not yet
listed in _data/gallery.yml and add them with EXIF metadata (date).

Usage:
    python3 scripts/sync_gallery.py [--dry-run] [--backfill-dates]

Options:
    --dry-run          Show what changes would be made without writing.
    --backfill-dates   Also update existing entries that are missing dates,
                       reading dates from EXIF data.

Requires: pip install Pillow pyyaml
"""

import os
import sys
from datetime import datetime

import yaml
from PIL import Image
from PIL.ExifTags import TAGS


def get_exif_date(filepath):
    """Extract the date taken from a photo's EXIF data. Returns a date or None."""
    try:
        img = Image.open(filepath)
        exif = img.getexif()
        if not exif:
            return None
        tags = {TAGS.get(k, k): v for k, v in exif.items()}
        # Check IFD EXIF sub-block for DateTimeOriginal
        ifd = exif.get_ifd(0x8769)  # ExifIFD
        if ifd:
            ifd_tags = {TAGS.get(k, k): v for k, v in ifd.items()}
            date_str = ifd_tags.get('DateTimeOriginal') or ifd_tags.get('DateTimeDigitized')
            if date_str:
                dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                return dt.date()
        # Fall back to top-level DateTime
        date_str = tags.get('DateTime')
        if not date_str:
            return None
        dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        return dt.date()
    except Exception:
        return None


def load_gallery(gallery_path):
    """Load gallery.yml and return (entries list, set of known image paths)."""
    if not os.path.exists(gallery_path):
        return [], set()
    with open(gallery_path, 'r') as f:
        entries = yaml.safe_load(f) or []
    known = set()
    for entry in entries:
        if entry and entry.get('image'):
            known.add(entry['image'])
    return entries, known


def scan_photos(photo_dir):
    """Return sorted list of photo filenames in the gallery directory."""
    extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    photos = []
    for f in sorted(os.listdir(photo_dir)):
        if os.path.splitext(f)[1].lower() in extensions:
            photos.append(f)
    return photos


def format_entry(image_path, date=None):
    """Format a gallery.yml entry as YAML text."""
    lines = [f"- image: {image_path}"]
    if date:
        lines.append(f"  date: {date.isoformat()}")
    return "\n".join(lines)


def main():
    dry_run = '--dry-run' in sys.argv
    backfill = '--backfill-dates' in sys.argv

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    gallery_yml = os.path.join(repo_root, '_data', 'gallery.yml')
    photo_dir = os.path.join(repo_root, 'assets', 'img', 'gallery')

    if not os.path.isdir(photo_dir):
        print(f"Gallery directory not found: {photo_dir}")
        sys.exit(1)

    entries, known_images = load_gallery(gallery_yml)
    photos = scan_photos(photo_dir)

    # Web path prefix for gallery images
    web_prefix = "/assets/img/gallery/"

    # Find new photos not in gallery.yml
    new_entries = []
    for filename in photos:
        web_path = web_prefix + filename
        if web_path in known_images:
            continue
        filepath = os.path.join(photo_dir, filename)
        date = get_exif_date(filepath)
        new_entries.append((web_path, date, filename))

    # Backfill dates for existing entries missing them
    backfilled = []
    if backfill:
        for entry in entries:
            if not entry or entry.get('date') or not entry.get('image'):
                continue
            image_path = entry['image']
            if not image_path.startswith(web_prefix):
                continue
            filename = image_path[len(web_prefix):]
            filepath = os.path.join(photo_dir, filename)
            if not os.path.exists(filepath):
                continue
            date = get_exif_date(filepath)
            if date:
                backfilled.append((entry, date, filename))

    # Report
    prefix = "[dry-run] " if dry_run else ""

    if new_entries:
        print(f"\n{prefix}Adding {len(new_entries)} new photo(s) to gallery.yml:\n")
        for web_path, date, filename in new_entries:
            date_str = f" (date: {date.isoformat()})" if date else " (no EXIF date)"
            print(f"  {prefix}{filename}{date_str}")
    else:
        print("\nNo new photos to add.")

    if backfilled:
        print(f"\n{prefix}Backfilling dates for {len(backfilled)} existing entry/entries:\n")
        for entry, date, filename in backfilled:
            print(f"  {prefix}{filename} -> date: {date.isoformat()}")
    elif backfill:
        print("\nNo existing entries need date backfill.")

    if dry_run:
        print(f"\nDry run complete. Use without --dry-run to apply changes.")
        return

    if not new_entries and not backfilled:
        return

    # Apply backfills to existing entries in memory
    for entry, date, _ in backfilled:
        entry['date'] = date

    # Append new entries to the gallery.yml file (preserving existing formatting)
    if new_entries:
        with open(gallery_yml, 'a') as f:
            f.write("\n")
            for web_path, date, _ in new_entries:
                f.write("\n" + format_entry(web_path, date) + "\n")

    # For backfills, we need to rewrite the relevant lines in the file
    if backfilled:
        with open(gallery_yml, 'r') as f:
            content = f.read()

        for entry, date, _ in backfilled:
            image_line = f"- image: {entry['image']}"
            date_line = f"  date: {date.isoformat()}"
            # Insert date line after the image line
            content = content.replace(
                image_line + "\n",
                image_line + "\n" + date_line + "\n",
                1
            )

        with open(gallery_yml, 'w') as f:
            f.write(content)

    total = len(new_entries) + len(backfilled)
    print(f"\nDone. Updated {total} entry/entries in gallery.yml.")


if __name__ == '__main__':
    main()
