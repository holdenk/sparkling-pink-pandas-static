# Sparkling Pink Pandas Website

Static website for the Sparkling Pink Pandas, a queer and trans-focused scooter and motorcycle group in San Francisco.

Built with Jekyll and deployed to GitHub Pages.

## Quick Start

### Prerequisites

- Ruby 3.x
- Bundler (`gem install bundler`)
- Git LFS (`git lfs install`)

### Local Development

```bash
git clone <repo-url>
cd sparklingpinkpandas-static-web
git lfs pull              # download large media files
bundle install            # install Ruby dependencies
bundle exec jekyll serve  # start local server at http://localhost:4000
```

## Adding Content

### Add an Event

The easiest way is to use the helper script:

```bash
python3 scripts/add_event.py
```

It will prompt you for the event details and create the markdown file.

To add an event manually, create a file in `_events/` named `YYYY-MM-DD-event-slug.md`:

```markdown
---
title: "My Event Title"
date: 2026-04-15
time: "2:00 PM"
location: "San Francisco, CA"
description: "Short description for event listings."
image: /assets/img/gallery/some-photo.jpg
map_url: "https://maps.google.com/..."
---

Full event description goes here. Markdown is supported.
```

The event will appear at `/events/YYYY/MM/event-slug/`.

**Fields:**
| Field | Required | Description |
|-------|----------|-------------|
| `title` | Yes | Event name |
| `date` | Yes | Date in YYYY-MM-DD format |
| `time` | No | Display time (e.g. "2:00 PM") |
| `location` | No | Where the event takes place |
| `description` | Yes | Short text for listings |
| `image` | No | Path to event image |
| `map_url` | No | Link to a route map |

### Add a Blog Post

Create a file in `_posts/` named `YYYY-MM-DD-post-title.md`:

```markdown
---
title: "Post Title"
author: "Your Name"
image: /assets/img/gallery/photo.jpg
---

Post content in markdown.
```

### Add Photos to the Gallery

1. Place images in `assets/img/gallery/`
2. Add an entry to `_data/gallery.yml`:

```yaml
- image: /assets/img/gallery/my-photo.jpg
  caption: "Description of the photo"
  date: 2026-01-15
  credit_name: Photographer Name
  credit_url: https://photographer-website.com
  instagram_url: https://www.instagram.com/sparklingpinkpandas/
```

All fields except `image` are optional.

### Add Videos

For YouTube videos, add the embed to `gallery.html` in the video section.

To store video files, place them in `assets/video/`. They are tracked via git LFS.

### Edit Social Links

Edit `_data/social.yml` to add or change social media links:

```yaml
- name: Instagram
  url: https://www.instagram.com/sparklingpinkpandas/
  icon: fab fa-instagram
```

Icons use [FontAwesome 5](https://fontawesome.com/v5/search) class names.

## Project Structure

```
_config.yml           # Jekyll configuration
_data/
  gallery.yml         # Gallery photo entries
  social.yml          # Social media links
_events/              # Event pages (markdown)
_posts/               # Blog posts (markdown)
_layouts/             # Page templates
  default.html        # Base layout (head, header, footer, scripts)
  event.html          # Single event page
  page.html           # Generic page (about, etc.)
  post.html           # Blog post page
_includes/            # Reusable template fragments
  header.html         # Site header and navigation
  footer.html         # Site footer
  event-card.html     # Event card for listings
  post-card.html      # Blog post card for listings
assets/
  css/site.css        # Custom styles (all other CSS is vendor)
  js/main.js          # Mobile menu toggle + lightbox init
  img/                # Site images
  img/gallery/        # Gallery photos (git LFS)
  video/              # Video files (git LFS)
scripts/
  add_event.py        # Helper script to create events
index.html            # Homepage
events.html           # Events listing (upcoming + past)
blog.html             # Blog listing
gallery.html          # Photo gallery + YouTube videos
about.md              # About page with mission, FAQ, press
events.ics            # iCal feed (auto-generated from events)
```

## Deployment

The site auto-deploys to GitHub Pages on push to `main` via GitHub Actions.

### GitHub Repository Setup

1. Go to **Settings > Pages** and set source to **GitHub Actions**
2. Go to **Settings > Secrets and variables**

### Required Secrets (for social media posting)

These are only needed if you want automatic social media posts when new events are added:

| Secret | Description |
|--------|-------------|
| `X_API_KEY` | Twitter/X API consumer key |
| `X_API_SECRET` | Twitter/X API consumer secret |
| `X_ACCESS_TOKEN` | Twitter/X access token |
| `X_ACCESS_SECRET` | Twitter/X access token secret |
| `BSKY_HANDLE` | Bluesky handle |
| `BSKY_PASSWORD` | Bluesky app password |
| `IG_USERNAME` | Instagram username |
| `IG_PASSWORD` | Instagram password |
| `SMTP_HOST` | SMTP server for email notifications |
| `SMTP_PORT` | SMTP port (usually 587) |
| `SMTP_USERNAME` | SMTP login email |
| `SMTP_PASSWORD` | SMTP password |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SITE_URL` | `https://sparklingpinkpandas.com` | Base URL for links in posts/emails |

### GitHub Actions Workflows

- **`jekyll.yml`** - Builds and deploys the site to GitHub Pages on every push to main
- **`post-social-media.yml`** - Posts to X, Bluesky, and Instagram when a new event is added
- **`notify-new-event.yml`** - Emails the Google Group when a new event is added

## Git LFS

Large files (images, videos) are tracked with git LFS. After cloning, run:

```bash
git lfs pull
```

Tracked extensions: jpg, jpeg, png, gif, webp, svg, bmp, tiff, tif, heic, heif, avif, ico, mp4, mov, avi, webm, mkv

## Tech Stack

- **Jekyll 4.3** - Static site generator
- **Bootstrap 4** - CSS framework
- **FontAwesome 5** - Icons
- **Magnific Popup** - Lightbox for gallery images
- **Google Fonts** - Roboto + Maven Pro
