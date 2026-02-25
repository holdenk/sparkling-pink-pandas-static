# Graphic & Manual Issues

Tasks that need a human with image editing tools.

## Logo Transparency

The panda-on-scooter logo (`assets/img/logo.png`) has a solid white background.
The pure white background around the panda should be made transparent (PNG alpha),
while keeping the white parts that are *part of the panda itself* (face, belly, etc.).

**Where it shows up:**
- Header (next to site title)
- Footer
- Favicon (`<link rel="shortcut icon">`)
- Open Graph / Twitter Card fallback image

**How to fix:**
Open `assets/img/logo.png` in an image editor (GIMP, Photoshop, Figma, etc.),
select the white background with a magic wand / select-by-color tool (being careful
not to select the panda's white fur), delete it, and re-export as PNG with
transparency. The panda currently sits on a clean white bg so this should be
straightforward with a low tolerance magic wand selection.

## Hero Image Optimization

`assets/img/hero1.jpg` is ~1.1 MB. It's used as a background image on every page
behind a pink overlay so fine detail isn't critical. Consider:
- Resizing to max 1920px wide
- Compressing to ~80% JPEG quality
- Could save 500KB+ without visible quality loss under the overlay

## Gallery Image Optimization

The 145+ gallery images in `assets/img/gallery/` are unoptimized originals.
Consider batch-converting to WebP (with JPEG fallback) or at minimum resizing
to a reasonable max dimension (e.g., 1600px) and compressing. This could
dramatically reduce page load time on the gallery page.
