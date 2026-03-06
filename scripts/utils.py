"""Shared utility functions for Sparkling Pink Pandas scripts."""

import os
import re
from datetime import date

import yaml

GALLERY_WEB_PREFIX = "/assets/img/gallery/"


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def load_gallery_yaml(gallery_path):
    """Load gallery.yml and return entries list.

    Returns an empty list if the file doesn't exist or is empty.
    """
    if not os.path.exists(gallery_path):
        return []
    with open(gallery_path, 'r') as f:
        return yaml.safe_load(f) or []


def gallery_known_images(entries):
    """Return set of image paths from gallery entries."""
    return {e['image'] for e in entries if e and e.get('image')}


def gallery_dated_photos(entries):
    """Return list of (image_path, date) for entries with valid dates."""
    dated = []
    for item in entries:
        if item and item.get('date'):
            item_date = item['date']
            if isinstance(item_date, date):
                dated.append((item['image'], item_date))
    return dated


def parse_event_file(filepath):
    """Parse a Jekyll event file's front matter.

    Returns (meta_dict, raw_fm_block, body_after_close) or None if invalid.
    """
    with open(filepath, 'r') as f:
        content = f.read()
    if not content.startswith('---'):
        return None
    close = content.find('\n---', 3)
    if close == -1:
        return None
    fm_raw = content[3:close]
    meta = yaml.safe_load(fm_raw) or {}
    rest = content[close + 4:]  # skip '\n---'
    return meta, fm_raw, rest


def update_event_frontmatter(filepath, fm_raw, rest, new_fields):
    """Add fields to an event's frontmatter and write the file.

    new_fields is a dict of key->value to append to the front matter.
    String values are quoted; others are written as-is.
    """
    additions = []
    for key, value in new_fields.items():
        if isinstance(value, str):
            additions.append(f'{key}: "{value}"')
        else:
            additions.append(f'{key}: {value}')
    new_fm = fm_raw.rstrip('\n') + '\n' + '\n'.join(additions) + '\n'
    new_content = '---' + new_fm + '---' + rest
    with open(filepath, 'w') as f:
        f.write(new_content)


def build_event_url(filename, site_url):
    """Build site URL from event filename.

    YYYY-MM-DD-slug.md -> {site_url}/events/YYYY/MM/slug/
    """
    parts = filename.replace('.md', '').split('-')
    year = parts[0]
    month = parts[1]
    slug = '-'.join(parts[3:])
    return f"{site_url}/events/{year}/{month}/{slug}/"


def insert_gallery_dates(gallery_yml_path, image_date_pairs):
    """Insert date lines into gallery.yml for the given (entry, date) pairs.

    Each pair is (entry_dict_with_image_key, date_object).
    Modifies the file in-place using string replacement.
    """
    with open(gallery_yml_path, 'r') as f:
        content = f.read()

    for entry, dt in image_date_pairs:
        image_line = f"- image: {entry['image']}"
        date_line = f"  date: {dt.isoformat()}"
        content = content.replace(
            image_line + "\n",
            image_line + "\n" + date_line + "\n",
            1
        )

    with open(gallery_yml_path, 'w') as f:
        f.write(content)


def apply_exif_orientation(img):
    """Rotate image according to EXIF orientation tag."""
    try:
        exif = img.getexif()
        orientation = exif.get(0x0112)
        if orientation == 3:
            img = img.rotate(180, expand=True)
        elif orientation == 6:
            img = img.rotate(270, expand=True)
        elif orientation == 8:
            img = img.rotate(90, expand=True)
    except Exception:
        pass
    return img


def resize_image(img, max_size):
    """Resize image so its largest dimension is at most max_size pixels.

    Returns the (possibly resized) image. Does nothing if already within bounds.
    """
    w, h = img.size
    if w <= max_size and h <= max_size:
        return img
    if w >= h:
        new_w = max_size
        new_h = int(h * (max_size / w))
    else:
        new_h = max_size
        new_w = int(w * (max_size / h))
    from PIL import Image
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)


def ensure_rgb(img):
    """Convert image to RGB mode if it isn't already."""
    if img.mode != 'RGB':
        return img.convert('RGB')
    return img
