# The Guide

Digital companion landing pages for businesses featured in our printed hotel
guides. Each advertiser gets a dedicated page reached via QR code from the
printed guide, designed for guests who've just landed — fast to load, easy
to act on, and on-brand with the guide itself.

## Structure

```
/
├── index.html                       Guide cover / advertiser index
├── assets/
│   ├── css/
│   │   ├── tokens.css               Shared design tokens (colour, type, spacing)
│   │   ├── guide.css                Shared component styles for advertiser pages
│   │   └── pages/
│   │       └── broken-bay-pearl-farm.css   Per-advertiser overrides & hero
│   └── img/
│       └── broken-bay-pearl-farm/   Per-advertiser imagery
├── broken-bay-pearl-farm/
│   └── index.html                   Advertiser landing page
└── README.md
```

## Design principles

1. **Mobile-first.** Pages are scanned from a printed guide at a hotel —
   most arrivals are on phones with patchy Wi-Fi. No build step, no
   framework, minimal JS.
2. **Actionable above the fold.** After the hero, the first thing a guest
   sees is a row of primary actions: *Book*, *Call*, *Directions*. These
   are the same on every advertiser page (familiar) but styled with the
   business's accent palette (unique).
3. **Elegant, not generic.** Each landing page leans into the
   business's own story — pearl-farm pages feel maritime and calm; a
   restaurant page would feel different. The shared layout grammar is what
   keeps the family of pages coherent.
4. **No tracking, no cookies, no popups.** Guests see the business; they
   don't see us.

## Adding a new advertiser

1. Copy `broken-bay-pearl-farm/` to `your-business-name/`.
2. Copy `assets/css/pages/broken-bay-pearl-farm.css` to a new file under
   the same folder; update the four accent variables at the top.
3. Drop hero and gallery images into `assets/img/your-business-name/`.
4. Replace copy, hours, contact details, and the action URLs (tel:, maps,
   booking link) in the HTML.

## Local preview

Any static server works:

```sh
python3 -m http.server 8000
# then visit http://localhost:8000/broken-bay-pearl-farm/
```

## Deployment

Push the repo to any static host (Netlify, Vercel, Cloudflare Pages,
GitHub Pages, S3+CloudFront). No build step required.
