# The Beachcomber Guide

A digital guide for guests of The Beachcomber Hotel & Resort in Toukley
on the NSW Central Coast. The guide is reached via QR code from a
printed companion placed in every room and covers the hotel itself,
the two on-site dining venues, and a curated set of nearby Central
Coast businesses.

## Site structure

```
/                                The hotel hero plus the four-category cover.
├── /hotel/                      Hotel info — about, amenities, on-site dining, contact.
├── /eat-and-drink/              Listings for restaurants, bars and food makers.
├── /things-to-do/               Listings for experiences, tours, retail and wellness.
├── /map/                        Interactive Leaflet map of every listing.
├── /{business-slug}/            One landing page per business (21 in total).
├── /assets/css/                 Shared styles + per-business palettes.
├── /_generator/                 Source of truth + scaffolding script.
└── README.md
```

## Four-category cover

The home page is split into four cards that match the printed guide:

1. **Hotel info** — the hotel's own page (description, facilities,
   check-in/out, on-site dining, contact).
2. **Eat & drink** — every restaurant, bar and food maker in the
   guide, including the two on-site venues. Sorted by drive time
   from the hotel.
3. **Things to do** — every experience, tour, retailer or wellness
   stop. Sorted by drive time from the hotel.
4. **Local map** — an interactive map showing the hotel plus every
   listing as a coloured pin. Tap a pin to read the basics and jump
   to the page.

## Standard business page

Every business page follows the same six-section layout:

1. Hero — full-bleed photo, white text on a black gradient, two pill
   tags (category + drive time from the hotel).
2. Primary CTAs — `Book` and/or `Visit website`.
3. Short description — eyebrow + headline + two paragraphs.
4. Guest offer — a perk for Beachcomber guests, with a redemption code.
5. Contact & social — icon tiles for any of: Call, Email, Directions,
   Instagram, Facebook, Website (tiles for missing channels are omitted).
6. Gallery — uniform 3-up square grid.

Every page links back to its category index via the guide bar, and
every page footer links back to the home cover.

## Design principles

1. **Mobile-first.** Every page is scanned from a printed guide at the
   hotel. No build step at deploy time, no framework, minimal JS.
2. **Standard layout, distinct identity.** Every business page uses
   the same shape so guests learn it once; per-business photography
   and an accent colour carry the personality.
3. **Bright, image-led, restrained.** White background, single
   sans-serif (Inter), photographs do the talking. Only black gradient
   overlays where they appear.
4. **No tracking, no cookies, no popups.**

## Adding or updating an advertiser

1. Edit `_generator/advertisers.json`. Each business object needs:
   - core fields: `name`, `slug`, `category`, `category_group`
     (either `eat-and-drink` or `things-to-do`), `suburb`,
     `distance_minutes` (from the hotel by car), `address`, `lat`,
     `lng`
   - contact fields where available: `phone`, `email`, `website`,
     `booking_url`, `instagram`, `facebook`
   - copy fields: `hero_subtitle`, `description_p1`, `description_p2`,
     `description_headline`, `offer_headline`, `offer_body`,
     `offer_code`, `accent_hex`
2. Run the generator:
   ```sh
   python3 _generator/build.py
   ```
3. Drop real photography into `assets/img/{slug}/` once commissioned,
   then swap the `picsum.photos` placeholder URLs in
   `{slug}/index.html` for the local paths. Placeholders are seeded
   by slug so each page is consistent between runs.

The generator is idempotent — re-running it regenerates the per-business
HTML, the per-business CSS, the four category pages, the map, and the
home cover. It does not touch images, shared CSS, or its own source.

## Hotel-specific fields

The `_generator/advertisers.json` file is shaped as
`{ "hotel": {...}, "advertisers": [...] }`. The `hotel` object carries
a few extra fields the standard advertiser doesn't need:

- `amenities` — array of short phrases shown on the hotel page
- `check_in`, `check_out` — displayed in the facilities block
- `description_p3` — a third paragraph that mentions the on-site
  dining venues (Pelicans Restaurant and Beachie Bar and Bistro)

## Map

The map page uses [Leaflet](https://leafletjs.com/) (loaded from a
CDN) with OpenStreetMap tiles. No API key required. Pins are
colour-coded:

- Black: the hotel
- Orange: eat & drink
- Green: things to do

The script reads every advertiser's `lat`/`lng` from the JSON at
generation time and inlines a small data array into `/map/index.html`.

## Local preview

```sh
python3 -m http.server 8000
# then visit http://localhost:8000/
```

## Deployment

Push the repo to any static host (Netlify, Vercel, Cloudflare Pages,
GitHub Pages, S3+CloudFront). **No build step is required at deploy
time** — the generator is a one-time authoring tool.
