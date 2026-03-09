#!/usr/bin/env python3
"""
Optimize gallery images by resizing and compressing them.

Resizes images to a maximum dimension (default 1600px) and compresses
JPEGs to a configurable quality level (default 82%). Preserves EXIF
orientation. Skips images already below the size threshold.

Usage:
    python3 scripts/optimize_gallery_images.py [OPTIONS]

Options:
    --dry-run           Show what would be changed without modifying files.
    --max-size PIXELS   Maximum width or height in pixels (default: 1600).
    --quality PERCENT   JPEG quality 1-100 (default: 82).
    --backup            Save originals to a backup directory before overwriting.

Requires: pip install Pillow
"""

import os
import shutil
import sys
from pathlib import Path

from PIL import Image

from utils import apply_exif_orientation, resize_image


def parse_args():
    args = {
        'dry_run': False,
        'max_size': 1600,
        'quality': 82,
        'backup': False,
    }
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == '--dry-run':
            args['dry_run'] = True
        elif argv[i] == '--backup':
            args['backup'] = True
        elif argv[i] == '--max-size' and i + 1 < len(argv):
            i += 1
            args['max_size'] = int(argv[i])
        elif argv[i] == '--quality' and i + 1 < len(argv):
            i += 1
            args['quality'] = int(argv[i])
        elif argv[i] in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        i += 1
    return args


def get_image_size_kb(filepath):
    return os.path.getsize(filepath) / 1024


def optimize_image(filepath, max_size, quality):
    """Resize and compress an image. Returns (new_width, new_height, saved_bytes) or None if skipped."""
    try:
        img = Image.open(filepath)
    except Exception as e:
        print(f"  Warning: Could not open {filepath}: {e}")
        return None

    original_size = os.path.getsize(filepath)

    img = apply_exif_orientation(img)
    img = resize_image(img, max_size)
    new_w, new_h = img.size

    # Convert RGBA/P to RGB for JPEG
    fmt = filepath.suffix.lower()
    if fmt in ('.jpg', '.jpeg'):
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        img.save(filepath, 'JPEG', quality=quality, optimize=True)
    elif fmt == '.png':
        img.save(filepath, 'PNG', optimize=True)
    elif fmt == '.webp':
        img.save(filepath, 'WEBP', quality=quality)
    else:
        return None

    new_size = os.path.getsize(filepath)
    saved = original_size - new_size

    return new_w, new_h, saved


def main():
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    gallery_dir = repo_root / 'assets' / 'img' / 'gallery'

    if not gallery_dir.is_dir():
        print(f"Gallery directory not found: {gallery_dir}")
        sys.exit(1)

    extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = sorted(
        p for p in gallery_dir.iterdir()
        if p.suffix.lower() in extensions
    )

    if not images:
        print("No images found in gallery directory.")
        return

    print(f"Found {len(images)} images in {gallery_dir}")
    print(f"Settings: max_size={args['max_size']}px, quality={args['quality']}%")

    if args['dry_run']:
        print("DRY RUN - no files will be modified.\n")

    # Backup directory
    backup_dir = None
    if args['backup'] and not args['dry_run']:
        backup_dir = repo_root / 'assets' / 'img' / 'gallery_backup'
        backup_dir.mkdir(exist_ok=True)
        print(f"Backing up originals to: {backup_dir}\n")

    total_saved = 0
    resized_count = 0
    skipped_count = 0

    for img_path in images:
        original_kb = get_image_size_kb(img_path)

        if args['dry_run']:
            try:
                img = Image.open(img_path)
                w, h = img.size
                img.close()
                needs_resize = w > args['max_size'] or h > args['max_size']
                status = "RESIZE" if needs_resize else "COMPRESS"
                print(f"  [{status}] {img_path.name} ({w}x{h}, {original_kb:.0f}KB)")
                if needs_resize:
                    resized_count += 1
                else:
                    skipped_count += 1
            except Exception as e:
                print(f"  [SKIP] {img_path.name}: {e}")
                skipped_count += 1
            continue

        # Backup original
        if backup_dir:
            shutil.copy2(img_path, backup_dir / img_path.name)

        result = optimize_image(img_path, args['max_size'], args['quality'])

        if result is None:
            skipped_count += 1
            continue

        new_w, new_h, saved = result
        new_kb = get_image_size_kb(img_path)
        total_saved += saved
        resized_count += 1

        if saved > 0:
            print(f"  {img_path.name}: {original_kb:.0f}KB -> {new_kb:.0f}KB ({new_w}x{new_h}, saved {saved / 1024:.0f}KB)")
        else:
            print(f"  {img_path.name}: {original_kb:.0f}KB -> {new_kb:.0f}KB (no savings)")

    print(f"\nProcessed: {resized_count}, Skipped: {skipped_count}")
    if not args['dry_run']:
        print(f"Total saved: {total_saved / 1024:.0f}KB ({total_saved / (1024 * 1024):.1f}MB)")
    if backup_dir:
        print(f"Originals backed up to: {backup_dir}")


if __name__ == '__main__':
    main()
