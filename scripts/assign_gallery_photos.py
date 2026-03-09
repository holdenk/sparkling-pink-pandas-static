#!/usr/bin/env python3
"""
For events without any photos, find a photo from the gallery that is
closest in time to the event (within 2 days) and assign it as the event's photo.

Usage:
    python3 scripts/assign_gallery_photos.py [--dry-run]

Options:
    --dry-run   Show what changes would be made without writing any files.
"""

import os
import sys
from datetime import date

from utils import gallery_dated_photos, load_gallery_yaml, parse_event_file


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

    entries = load_gallery_yaml(gallery_path)
    dated_photos = gallery_dated_photos(entries)
    if not dated_photos:
        print("No dated gallery photos found. Nothing to do.")
        return

    assigned = 0
    for filename in sorted(os.listdir(events_dir)):
        if not filename.endswith('.md'):
            continue

        filepath = os.path.join(events_dir, filename)
        result = parse_event_file(filepath)
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
        if days_diff > 2:
            continue  # no gallery photo within ±2 days of this event

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
