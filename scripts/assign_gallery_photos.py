#!/usr/bin/env python3
"""
For events without any photos, find a photo from the gallery that is
closest in time to the event and assign it as the event's photo.

Usage:
    python3 scripts/assign_gallery_photos.py [--dry-run]

Options:
    --dry-run   Show what changes would be made without writing any files.
"""

import os
import re
import sys
from datetime import date

import yaml


def load_gallery(gallery_path):
    """Load gallery items that have dates."""
    with open(gallery_path, 'r') as f:
        gallery = yaml.safe_load(f)
    dated = []
    for item in gallery:
        if item.get('date'):
            item_date = item['date']
            if isinstance(item_date, date):
                dated.append((item['image'], item_date))
    return dated


def parse_event(filepath):
    """Return (front_matter_dict, raw_fm_block, body_after_close_fence) or None."""
    with open(filepath, 'r') as f:
        content = f.read()
    if not content.startswith('---'):
        return None
    close = content.find('\n---', 3)
    if close == -1:
        return None
    fm_raw = content[3:close]
    fm = yaml.safe_load(fm_raw) or {}
    rest = content[close + 4:]  # skip '\n---'
    return fm, fm_raw, rest


def find_closest_photo(event_date, dated_photos):
    """Return (image_path, photo_date) whose date is closest to event_date, or None."""
    if not dated_photos:
        return None
    return min(dated_photos, key=lambda p: abs((p[1] - event_date).days))


def add_image_to_front_matter(fm_raw, image_path):
    """Insert an image field before the closing --- of the front matter block."""
    return fm_raw.rstrip('\n') + f'\nimage: {image_path}\n'


def main():
    dry_run = '--dry-run' in sys.argv

    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)

    gallery_path = os.path.join(repo_root, '_data', 'gallery.yml')
    events_dir = os.path.join(repo_root, '_events')

    dated_photos = load_gallery(gallery_path)
    if not dated_photos:
        print("No dated gallery photos found. Nothing to do.")
        return

    assigned = 0
    for filename in sorted(os.listdir(events_dir)):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(events_dir, filename)
        result = parse_event(filepath)
        if result is None:
            continue

        fm, fm_raw, rest = result

        if fm.get('image'):
            continue  # already has a photo

        event_date = fm.get('date')
        if event_date is None:
            continue
        if not isinstance(event_date, date):
            continue

        closest_image, closest_date = find_closest_photo(event_date, dated_photos)
        if closest_image is None:
            continue

        days_diff = abs((closest_date - event_date).days)
        print(f"{'[dry-run] ' if dry_run else ''}Assigning {closest_image} to {filename} "
              f"(closest gallery photo is {days_diff} day(s) away)")

        if not dry_run:
            new_fm_raw = add_image_to_front_matter(fm_raw, closest_image)
            new_content = '---' + new_fm_raw + '---' + rest
            with open(filepath, 'w') as f:
                f.write(new_content)

        assigned += 1

    print(f"\n{'Would assign' if dry_run else 'Assigned'} photos to {assigned} event(s).")


if __name__ == '__main__':
    main()
