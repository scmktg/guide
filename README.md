# The Guide

Digital companion landing pages for businesses featured in our printed
hotel guides. Each advertiser gets a dedicated page reached via QR code
from the printed guide, designed for guests who've just landed — fast
to load, easy to act on, and on-brand with the guide itself.

## Structure

```
/
├── index.html                       Guide cover / advertiser index
├── assets/
│   ├── css/
│   │   ├── tokens.css               Shared design tokens (colour, type, spacing)
│   │   ├── guide.css                Shared component styles for advertiser pages
│   │   └── pages/
│   │       └── {slug}.css           Per-advertiser palette (one per business)
│   └── img/
│       └── {slug}/                  Per-advertiser imagery (when commissioned)
├── {slug}/
│   └── index.html                   Advertiser landing page (one per business)
├── _generator/
│   ├── advertisers.json             Source of truth for every advertiser
│   └── build.py                     Scaffolding script — regenerates pages
└── README.md
```

## Standard page template

Every advertiser page follows the same six-section layout:

1. **Hero** — full-bleed photograph, white text on a black-only gradient
   overlay, with the business name plus two pill tags (category and
   driving time from the partner hotels).
2. **Primary CTAs** — `Book` (or `Visit website`) plus a ghost
   `Visit website` button when both a booking link and a site exist.
3. **Short description** — eyebrow, headline, two short paragraphs.
4. **Guest offer** — a soft-grey card with the offer headline, redemption
   instructions and a monospaced code (e.g. `GUIDE / PEARL`).
5. **Contact &amp; social** — icon tiles for any of: Call, Email,
   Directions, Instagram, Facebook, Website. Tiles for missing channels
   are simply omitted.
6. **Gallery** — uniform 3-up square grid.

The structure is identical across every page. The only per-advertiser
file is `assets/css/pages/{slug}.css`, which just defines an `--accent`
colour. All copy lives in the page HTML.

## Design principles

1. **Mobile-first.** Pages are scanned from a printed guide at a hotel —
   most arrivals are on phones with patchy Wi-Fi. No build step at deploy
   time, no framework, minimal JS.
2. **Standard layout, distinct identity.** Every page uses the same
   structure so guests learn it once; per-advertiser photographs and an
   accent colour carry the personality.
3. **Bright, image-led, restrained.** White background, single sans-serif
   (Inter), photographs do the talking. Only black gradient overlays
   anywhere they appear.
4. **No tracking, no cookies, no popups.** Guests see the business; they
   don't see us.

## Adding or updating an advertiser

1. Edit `_generator/advertisers.json` — add a new object, or update
   fields on an existing one. Every field is documented by example in
   the existing entries.
2. Run the generator:
   ```sh
   python3 _generator/build.py
   ```
3. Drop real photography into `assets/img/{slug}/` when commissioned,
   then swap the `picsum.photos` placeholder URLs in `{slug}/index.html`
   for the local paths. (Placeholder URLs are seeded by slug so each
   page is consistent between runs.)

The generator is idempotent — re-running it overwrites
`{slug}/index.html`, `assets/css/pages/{slug}.css` and the root
`index.html`. It does **not** touch images, shared CSS or any custom
edits to the generator itself.

## Local preview

Any static server works:

```sh
python3 -m http.server 8000
# then visit http://localhost:8000/
```

## Deployment

Push the repo to any static host (Netlify, Vercel, Cloudflare Pages,
GitHub Pages, S3+CloudFront). **No build step is required at deploy
time** — the generator is a one-time authoring tool, not part of the
deploy pipeline.
