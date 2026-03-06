#!/usr/bin/env python3
"""
Convert gallery images to WebP format and generate thumbnails.

Converts all JPEG/PNG images in assets/img/gallery/ to WebP, generates
smaller thumbnails for the gallery grid, updates references in
_data/gallery.yml, _events/*.md front matter, and assets/css/site.css.

Also converts the hero image (assets/img/hero1.jpg) to WebP.

Usage:
    python3 scripts/convert_to_webp.py [OPTIONS]

Options:
    --dry-run           Show what would be changed without modifying files.
    --quality PERCENT   WebP quality 1-100 (default: 80).
    --max-size PIXELS   Maximum width or height in pixels (default: 1600).
    --thumb-height PX   Thumbnail height in pixels (default: 400).
    --no-thumbnails     Skip thumbnail generation.
    --no-delete         Keep original files after conversion.

Requires: pip install Pillow
"""

import re
import sys
from pathlib import Path

from PIL import Image

from utils import apply_exif_orientation, ensure_rgb, resize_image


def parse_args():
    args = {
        'dry_run': False,
        'quality': 80,
        'max_size': 1600,
        'thumb_height': 400,
        'thumbnails': True,
        'delete_originals': False,
    }
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == '--dry-run':
            args['dry_run'] = True
        elif argv[i] == '--no-thumbnails':
            args['thumbnails'] = False
        elif argv[i] == '--no-delete':
            args['delete_originals'] = False
        elif argv[i] == '--quality' and i + 1 < len(argv):
            i += 1
            args['quality'] = int(argv[i])
        elif argv[i] == '--max-size' and i + 1 < len(argv):
            i += 1
            args['max_size'] = int(argv[i])
        elif argv[i] == '--thumb-height' and i + 1 < len(argv):
            i += 1
            args['thumb_height'] = int(argv[i])
        elif argv[i] in ('-h', '--help'):
            print(__doc__)
            sys.exit(0)
        i += 1
    return args


def convert_image(src_path, gallery_dir, thumbs_dir, args):
    """Convert a single image to WebP and optionally generate a thumbnail.

    Returns (webp_path, original_size, webp_size, thumb_size) or None on error.
    """
    try:
        img = Image.open(src_path)
    except Exception as e:
        print(f"  Warning: Could not open {src_path.name}: {e}")
        return None

    original_size = src_path.stat().st_size
    img = apply_exif_orientation(img)
    img = resize_image(img, args['max_size'])
    img = ensure_rgb(img)

    # Save full-size WebP
    webp_name = src_path.stem + '.webp'
    webp_path = gallery_dir / webp_name
    img.save(webp_path, 'WEBP', quality=args['quality'], method=4)
    webp_size = webp_path.stat().st_size

    # Generate thumbnail
    thumb_size = 0
    if args['thumbnails'] and thumbs_dir:
        thumb_height = args['thumb_height']
        curr_w, curr_h = img.size
        if curr_h > thumb_height:
            ratio = thumb_height / curr_h
            thumb_w = int(curr_w * ratio)
            thumb = img.resize((thumb_w, thumb_height), Image.Resampling.LANCZOS)
        else:
            thumb = img
        thumb_path = thumbs_dir / webp_name
        thumb.save(thumb_path, 'WEBP', quality=max(args['quality'] - 5, 50), method=4)
        thumb_size = thumb_path.stat().st_size

    # Delete original
    if args['delete_originals'] and src_path.suffix.lower() != '.webp':
        print(f"Deleting {src_path}")
        src_path.unlink()

    return webp_path, original_size, webp_size, thumb_size


def update_references(repo_root, dry_run=False):
    """Update image references from .jpg/.jpeg/.png to .webp in gallery.yml,
    events, and CSS."""
    ext_pattern = re.compile(
        r'(/?assets/img/gallery/[^\s"\']+)\.(jpg|jpeg|png|JPG|JPEG|PNG)'
    )
    hero_pattern = re.compile(r'hero1\.(jpg|jpeg|png)')

    files_updated = []

    # Update gallery.yml
    gallery_yml = repo_root / '_data' / 'gallery.yml'
    if gallery_yml.exists():
        content = gallery_yml.read_text()
        new_content = ext_pattern.sub(r'\1.webp', content)
        if new_content != content:
            if not dry_run:
                gallery_yml.write_text(new_content)
            files_updated.append(str(gallery_yml.relative_to(repo_root)))

    # Update event front matter
    events_dir = repo_root / '_events'
    if events_dir.is_dir():
        for event_file in sorted(events_dir.glob('*.md')):
            content = event_file.read_text()
            new_content = ext_pattern.sub(r'\1.webp', content)
            if new_content != content:
                if not dry_run:
                    event_file.write_text(new_content)
                files_updated.append(str(event_file.relative_to(repo_root)))

    # Update CSS (hero image)
    css_file = repo_root / 'assets' / 'css' / 'site.css'
    if css_file.exists():
        content = css_file.read_text()
        new_content = hero_pattern.sub('hero1.webp', content)
        if new_content != content:
            if not dry_run:
                css_file.write_text(new_content)
            files_updated.append(str(css_file.relative_to(repo_root)))

    return files_updated


def convert_hero_image(repo_root, args):
    """Convert the hero image to WebP."""
    img_dir = repo_root / 'assets' / 'img'
    hero_src = None
    for ext in ('.jpg', '.jpeg', '.png'):
        candidate = img_dir / f'hero1{ext}'
        if candidate.exists():
            hero_src = candidate
            break

    if not hero_src:
        return None

    original_size = hero_src.stat().st_size

    try:
        img = Image.open(hero_src)
    except Exception as e:
        print(f"  Warning: Could not open hero image: {e}")
        return None

    img = apply_exif_orientation(img)
    img = ensure_rgb(img)

    hero_webp = img_dir / 'hero1.webp'
    img.save(hero_webp, 'WEBP', quality=args['quality'], method=4)
    webp_size = hero_webp.stat().st_size

    if args['delete_originals']:
        hero_src.unlink()

    return original_size, webp_size


def main():
    args = parse_args()

    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent
    gallery_dir = repo_root / 'assets' / 'img' / 'gallery'

    if not gallery_dir.is_dir():
        print(f"Gallery directory not found: {gallery_dir}")
        sys.exit(1)

    # Collect source images
    extensions = {'.jpg', '.jpeg', '.png'}
    images = sorted(
        p for p in gallery_dir.iterdir()
        if p.is_file() and p.suffix.lower() in extensions
    )

    if not images:
        print("No JPEG/PNG images found in gallery directory.")
        print("(Images may already be converted to WebP.)")
        return

    print(f"Found {len(images)} images to convert in {gallery_dir}")
    print(f"Settings: quality={args['quality']}%, max_size={args['max_size']}px", end="")
    if args['thumbnails']:
        print(f", thumb_height={args['thumb_height']}px")
    else:
        print(" (no thumbnails)")

    if args['dry_run']:
        print("\nDRY RUN — no files will be modified.\n")

    # Set up thumbnails directory
    thumbs_dir = None
    if args['thumbnails']:
        thumbs_dir = gallery_dir / 'thumbs'
        if not args['dry_run']:
            thumbs_dir.mkdir(exist_ok=True)

    total_original = 0
    total_webp = 0
    total_thumbs = 0
    converted = 0
    errors = 0

    for src_path in images:
        original_kb = src_path.stat().st_size / 1024

        if args['dry_run']:
            try:
                img = Image.open(src_path)
                w, h = img.size
                img.close()
                needs_resize = w > args['max_size'] or h > args['max_size']
                resize_str = f" -> resize to {args['max_size']}px" if needs_resize else ""
                print(f"  {src_path.name} ({w}x{h}, {original_kb:.0f}KB){resize_str} -> .webp")
            except Exception as e:
                print(f"  {src_path.name}: ERROR - {e}")
                errors += 1
            converted += 1
            continue

        result = convert_image(src_path, gallery_dir, thumbs_dir, args)

        if result is None:
            errors += 1
            continue

        _, original_size, webp_size, thumb_size = result
        total_original += original_size
        total_webp += webp_size
        total_thumbs += thumb_size
        converted += 1

        saved_pct = (1 - webp_size / original_size) * 100 if original_size > 0 else 0
        thumb_str = f", thumb {thumb_size / 1024:.0f}KB" if thumb_size > 0 else ""
        print(f"  {src_path.name}: {original_size / 1024:.0f}KB -> {webp_size / 1024:.0f}KB ({saved_pct:.0f}% smaller){thumb_str}")

    # Convert hero image
    print("\nHero image:")
    if args['dry_run']:
        hero_src = repo_root / 'assets' / 'img' / 'hero1.jpg'
        if hero_src.exists():
            print(f"  hero1.jpg ({hero_src.stat().st_size / 1024:.0f}KB) -> hero1.webp")
        else:
            print("  No hero1.jpg found (may already be converted)")
    else:
        hero_result = convert_hero_image(repo_root, args)
        if hero_result:
            orig, webp = hero_result
            saved_pct = (1 - webp / orig) * 100 if orig > 0 else 0
            print(f"  hero1.jpg: {orig / 1024:.0f}KB -> {webp / 1024:.0f}KB ({saved_pct:.0f}% smaller)")
            total_original += orig
            total_webp += webp
        else:
            print("  No hero image found to convert")

    # Update references
    print("\nUpdating references...")
    updated_files = update_references(repo_root, dry_run=args['dry_run'])
    if updated_files:
        for f in updated_files:
            print(f"  Updated: {f}")
    else:
        print("  No references needed updating")

    # Summary
    print(f"\n{'=' * 50}")
    print(f"Converted: {converted} images")
    if errors:
        print(f"Errors: {errors}")
    if not args['dry_run'] and total_original > 0:
        saved = total_original - total_webp
        saved_pct = (saved / total_original) * 100
        print(f"Original total:  {total_original / (1024 * 1024):.1f} MB")
        print(f"WebP total:      {total_webp / (1024 * 1024):.1f} MB")
        if total_thumbs > 0:
            print(f"Thumbnails:      {total_thumbs / (1024 * 1024):.1f} MB")
        print(f"Saved:           {saved / (1024 * 1024):.1f} MB ({saved_pct:.0f}%)")
    if updated_files:
        print(f"Files updated:   {len(updated_files)}")


if __name__ == '__main__':
    main()
