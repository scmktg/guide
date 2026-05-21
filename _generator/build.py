#!/usr/bin/env python3
"""
The Guide — page generator.

Reads _generator/advertisers.json and writes a fresh page for each
advertiser. This is a one-time scaffolding tool: run it after editing
the JSON to add or update an advertiser, then commit the generated
files. The deployed site itself is fully static and needs no build.

Usage:
  python3 _generator/build.py

Generates:
  /{slug}/index.html               One per advertiser
  /assets/css/pages/{slug}.css     One per advertiser (palette only)
  /index.html                      The directory of all advertisers
"""

import html
import json
import os
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_generator" / "advertisers.json"
PAGES_CSS = ROOT / "assets" / "css" / "pages"

# ── Helpers ──────────────────────────────────────────────────────────────

def hero_img(slug: str) -> str:
    return f"https://picsum.photos/seed/{slug}-hero/2400/1400"

def gallery_img(slug: str, n: int) -> str:
    return f"https://picsum.photos/seed/{slug}-g{n}/900/900"

def tel_href(phone: str) -> str:
    if not phone:
        return ""
    clean = "".join(c for c in phone if c.isdigit() or c == "+")
    if clean.startswith("0"):
        clean = "+61" + clean[1:]
    return f"tel:{clean}"

def directions_url(name: str, address: str | None) -> str:
    q = f"{name} {address}" if address else name
    return "https://maps.google.com/?q=" + urllib.parse.quote_plus(q)

def hero_name_html(name: str) -> str:
    """Split business name across two lines around its midpoint."""
    words = name.split()
    if len(words) == 1:
        return html.escape(name)
    if len(words) == 2:
        return f"{html.escape(words[0])}<br/>{html.escape(words[1])}"
    target = len(name) // 2
    cum, best_i, best_diff = 0, 1, 10**9
    for i, w in enumerate(words[:-1]):
        cum += len(w) + 1
        diff = abs(cum - target)
        if diff < best_diff:
            best_diff, best_i = diff, i + 1
    first = " ".join(words[:best_i])
    second = " ".join(words[best_i:])
    return f"{html.escape(first)}<br/>{html.escape(second)}"

# ── SVG icon strings ─────────────────────────────────────────────────────

ICON_CATEGORY = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <circle cx="12" cy="12" r="3"/>
            <path d="M4 12c2-4 5-6 8-6s6 2 8 6c-2 4-5 6-8 6s-6-2-8-6z"/>
          </svg>"""

ICON_PIN = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">
            <path d="M12 21s-7-7.5-7-12a7 7 0 0 1 14 0c0 4.5-7 12-7 12z"/>
            <circle cx="12" cy="9" r="2.5"/>
          </svg>"""

ICON_PHONE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
          <path d="M5 4h3l2 5-2.5 1.5a12 12 0 0 0 6 6L15 14l5 2v3a2 2 0 0 1-2 2A15 15 0 0 1 3 6a2 2 0 0 1 2-2z"/>
        </svg>"""

ICON_EMAIL = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
          <rect x="3" y="5" width="18" height="14" rx="2"/>
          <path d="M3 7l9 6 9-6"/>
        </svg>"""

ICON_PIN_SMALL = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
          <path d="M12 21s-7-7.5-7-12a7 7 0 0 1 14 0c0 4.5-7 12-7 12z"/>
          <circle cx="12" cy="9" r="2.5"/>
        </svg>"""

ICON_INSTAGRAM = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
          <rect x="3.5" y="3.5" width="17" height="17" rx="4.5"/>
          <circle cx="12" cy="12" r="3.8"/>
          <circle cx="17.3" cy="6.7" r="1" fill="currentColor" stroke="none"/>
        </svg>"""

ICON_FACEBOOK = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
          <path d="M15 8h2.5V5H15a3.5 3.5 0 0 0-3.5 3.5V11H9v3h2.5v7h3v-7H17l.5-3h-3V8.5A.5.5 0 0 1 15 8z"/>
        </svg>"""

ICON_WEBSITE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true">
          <circle cx="12" cy="12" r="9"/>
          <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>
        </svg>"""

def render_contact_tiles(adv: dict) -> str:
    tiles: list[str] = []
    if adv.get("phone"):
        tiles.append(f"""<a class="contact-tile" href="{tel_href(adv['phone'])}" aria-label="Call">
        {ICON_PHONE}
        <span class="contact-tile__label">Call</span>
      </a>""")
    if adv.get("email"):
        tiles.append(f"""<a class="contact-tile" href="mailto:{adv['email']}" aria-label="Email">
        {ICON_EMAIL}
        <span class="contact-tile__label">Email</span>
      </a>""")
    if adv.get("address"):
        tiles.append(f"""<a class="contact-tile" href="{directions_url(adv['name'], adv['address'])}" aria-label="Directions">
        {ICON_PIN_SMALL}
        <span class="contact-tile__label">Directions</span>
      </a>""")
    if adv.get("instagram"):
        tiles.append(f"""<a class="contact-tile" href="{adv['instagram']}" aria-label="Instagram">
        {ICON_INSTAGRAM}
        <span class="contact-tile__label">Instagram</span>
      </a>""")
    if adv.get("facebook"):
        tiles.append(f"""<a class="contact-tile" href="{adv['facebook']}" aria-label="Facebook">
        {ICON_FACEBOOK}
        <span class="contact-tile__label">Facebook</span>
      </a>""")
    if adv.get("website"):
        tiles.append(f"""<a class="contact-tile" href="{adv['website']}" aria-label="Website">
        {ICON_WEBSITE}
        <span class="contact-tile__label">Website</span>
      </a>""")
    return "\n      ".join(tiles)

def render_cta_block(adv: dict) -> str:
    buttons = []
    primary = adv.get("booking_url") or adv.get("website")
    if primary:
        label = "Book" if adv.get("booking_url") else "Visit website"
        buttons.append(f'<a class="btn" href="{primary}">{label}</a>')
    if adv.get("website") and adv.get("booking_url"):
        buttons.append(f'<a class="btn btn--ghost" href="{adv["website"]}">Visit website</a>')
    if not buttons and adv.get("address"):
        buttons.append(f'<a class="btn" href="{directions_url(adv["name"], adv["address"])}">Get directions</a>')
    if not buttons:
        return ""
    rendered = "\n    ".join(buttons)
    return f"""<!-- ─── Primary CTAs ───────────────────────────────────────────── -->
  <div class="cta-row">
    {rendered}
  </div>
"""

def render_contacts_block(adv: dict) -> str:
    tiles = render_contact_tiles(adv)
    if not tiles.strip():
        return ""
    return f"""<!-- ─── Contact + social ───────────────────────────────────────── -->
  <section class="contacts" aria-label="Contact and social">
    <div class="contacts__grid">
      {tiles}
    </div>
  </section>
"""

# ── HTML template ────────────────────────────────────────────────────────

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>{name} — featured in The Guide</title>
  <meta name="description" content="{meta_description}" />

  <meta name="theme-color" content="#FFFFFF" />
  <meta property="og:title" content="{name}" />
  <meta property="og:description" content="{meta_description}" />
  <meta property="og:type" content="website" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="preconnect" href="https://picsum.photos" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />

  <link rel="stylesheet" href="/assets/css/tokens.css" />
  <link rel="stylesheet" href="/assets/css/guide.css" />
  <link rel="stylesheet" href="/assets/css/pages/{slug}.css" />
</head>
<body>

  <!-- ─── Hero ───────────────────────────────────────────────────── -->
  <section class="hero">
    <header class="guide-bar">
      <a class="guide-bar__mark" href="/">The Guide</a>
      <span>Central Coast</span>
    </header>

    <picture class="hero__art" aria-hidden="true">
      <img
        src="{hero_image}"
        alt=""
        loading="eager"
        fetchpriority="high"
      />
    </picture>

    <div class="hero__inner">
      <div class="hero__tags rise rise--1">
        <span class="hero__tag">
          {icon_category}
          {category}
        </span>
        <span class="hero__tag">
          {icon_pin}
          {distance_minutes} min from your hotel
        </span>
      </div>
      <h1 class="rise rise--2">{hero_name_html}</h1>
      <p class="hero__sub rise rise--3">
        {hero_subtitle}
      </p>
    </div>
  </section>

  {cta_block}
  <!-- ─── Short description ──────────────────────────────────────── -->
  <section class="description">
    <p class="eyebrow">About</p>
    <h2>{description_headline}</h2>
    <p>{description_p1}</p>
    <p>{description_p2}</p>
  </section>

  <!-- ─── Guest offer ────────────────────────────────────────────── -->
  <aside class="offer" aria-label="Offer for Guide readers">
    <span class="offer__label">For Guide readers</span>
    <h3>{offer_headline}</h3>
    <p>{offer_body}</p>
    <span class="offer__code">{offer_code}</span>
  </aside>

  {contacts_block}

  <!-- ─── Gallery ────────────────────────────────────────────────── -->
  <section class="gallery-section" aria-label="Gallery">
    <header class="gallery-section__head">
      <p class="eyebrow">Gallery</p>
      <h2>{gallery_headline}</h2>
    </header>
    <div class="gallery">
      <figure class="gallery__tile"><img src="{g1}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g2}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g3}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g4}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g5}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g6}" alt="" loading="lazy" /></figure>
    </div>
  </section>

  <!-- ─── Guide foot ─────────────────────────────────────────────── -->
  <footer class="guide-foot">
    <strong>You found us through The Guide.</strong>
    A curated companion to the Central Coast, placed in the rooms of fine hotels nearby. <a href="/">See the full guide</a>.
  </footer>

</body>
</html>
"""

CSS_TEMPLATE = """/* {name} — per-advertiser palette. Generated from advertisers.json. */

:root {{
  --accent:     {accent};
  --accent-ink: #FFFFFF;
}}
"""

# ── Root index template ─────────────────────────────────────────────────

INDEX_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>The Guide — Companion to the Printed Edition</title>
  <meta name="description" content="A curated companion to the Central Coast, placed in the rooms of fine hotels nearby." />
  <meta name="theme-color" content="#FFFFFF" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
  <link rel="stylesheet" href="/assets/css/tokens.css" />
  <style>
    body {{
      margin: 0;
      font-family: var(--font-sans);
      background: var(--paper);
      color: var(--ink);
      -webkit-font-smoothing: antialiased;
    }}
    .wrap {{
      max-width: 72rem;
      margin: 0 auto;
      padding: clamp(3rem, 8vw, 6rem) clamp(1.25rem, 4vw, 2.5rem);
    }}
    .head {{ text-align: center; margin: 0 auto clamp(2.5rem, 6vw, 4rem); max-width: 40rem; }}
    .eyebrow {{
      display: inline-block;
      font-size: 0.78rem;
      font-weight: 500;
      letter-spacing: 0.22em;
      text-transform: uppercase;
      color: var(--ink-muted);
      margin: 0 0 1rem;
    }}
    h1 {{
      font-weight: 600;
      letter-spacing: -0.03em;
      font-size: clamp(2.2rem, 1.6rem + 2.6vw, 3.6rem);
      line-height: 1.05;
      margin: 0 0 1.2rem;
      text-wrap: balance;
    }}
    .head p {{
      color: var(--ink-soft);
      font-size: clamp(1rem, 0.95rem + 0.25vw, 1.12rem);
      line-height: 1.6;
      margin: 0 auto;
      max-width: 34rem;
    }}
    .grid {{
      display: grid;
      gap: 0.75rem;
      grid-template-columns: 1fr;
    }}
    @media (min-width: 640px) {{ .grid {{ grid-template-columns: repeat(2, 1fr); }} }}
    @media (min-width: 980px) {{ .grid {{ grid-template-columns: repeat(3, 1fr); }} }}
    .card {{
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      padding: 1.4rem 1.5rem;
      border: 1px solid var(--rule);
      border-radius: 14px;
      background: var(--paper);
      color: var(--ink);
      transition:
        border-color 0.2s var(--ease),
        transform 0.2s var(--ease),
        box-shadow 0.2s var(--ease);
    }}
    .card:hover {{
      border-color: var(--ink);
      transform: translateY(-2px);
      box-shadow: 0 14px 28px -20px rgba(17,17,19,0.22);
    }}
    .card__category {{
      font-size: 0.74rem;
      font-weight: 500;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--ink-muted);
    }}
    .card__name {{
      font-size: 1.18rem;
      font-weight: 600;
      letter-spacing: -0.015em;
      color: var(--ink);
    }}
    .card__meta {{
      margin-top: 0.5rem;
      font-size: 0.88rem;
      color: var(--ink-soft);
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .card__meta::after {{
      content: "›";
      margin-left: auto;
      font-size: 1.2em;
      color: var(--ink-muted);
      transition: transform 0.2s var(--ease), color 0.2s var(--ease);
    }}
    .card:hover .card__meta::after {{ transform: translateX(3px); color: var(--ink); }}
    .foot {{
      margin-top: clamp(3rem, 6vw, 4.5rem);
      padding-top: 2.5rem;
      border-top: 1px solid var(--rule);
      text-align: center;
      font-size: 0.85rem;
      color: var(--ink-muted);
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <header class="head">
      <p class="eyebrow">The Guide · Central Coast</p>
      <h1>The companion to the printed edition.</h1>
      <p>
        You've probably arrived here by scanning a QR code from the
        guide in your room. Every business featured in print has its
        own page — pick yours below.
      </p>
    </header>

    <div class="grid">
      {cards}
    </div>

    <footer class="foot">A curated companion to the Central Coast, placed in the rooms of fine hotels nearby.</footer>
  </main>
</body>
</html>
"""

def render_index(advertisers: list[dict]) -> str:
    cards = []
    for a in sorted(advertisers, key=lambda x: x["name"].lower()):
        cards.append(f"""<a class="card" href="/{a['slug']}/">
        <span class="card__category">{html.escape(a['category'])}</span>
        <span class="card__name">{html.escape(a['name'])}</span>
        <span class="card__meta">{html.escape(a['suburb'])} · {a['distance_minutes']} min</span>
      </a>""")
    return INDEX_TEMPLATE.format(cards="\n      ".join(cards))

# ── Main ────────────────────────────────────────────────────────────────

def main() -> None:
    with open(DATA, "r", encoding="utf-8") as f:
        advertisers = json.load(f)

    PAGES_CSS.mkdir(parents=True, exist_ok=True)

    for a in advertisers:
        slug = a["slug"]

        # HTML
        page_dir = ROOT / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        page_html = PAGE_TEMPLATE.format(
            name=html.escape(a["name"]),
            meta_description=html.escape(a["hero_subtitle"]),
            slug=slug,
            hero_image=hero_img(slug),
            icon_category=ICON_CATEGORY,
            icon_pin=ICON_PIN,
            category=html.escape(a["category"]),
            distance_minutes=a["distance_minutes"],
            hero_name_html=hero_name_html(a["name"]),
            hero_subtitle=html.escape(a["hero_subtitle"]),
            cta_block=render_cta_block(a),
            contacts_block=render_contacts_block(a),
            description_headline=html.escape(a["description_headline"]),
            description_p1=html.escape(a["description_p1"]),
            description_p2=html.escape(a["description_p2"]),
            offer_headline=html.escape(a["offer_headline"]),
            offer_body=html.escape(a["offer_body"]),
            offer_code=html.escape(a["offer_code"]),
            gallery_headline=html.escape(f"From {a['suburb']}."),
            g1=gallery_img(slug, 1),
            g2=gallery_img(slug, 2),
            g3=gallery_img(slug, 3),
            g4=gallery_img(slug, 4),
            g5=gallery_img(slug, 5),
            g6=gallery_img(slug, 6),
        )
        (page_dir / "index.html").write_text(page_html, encoding="utf-8")

        # CSS
        css = CSS_TEMPLATE.format(name=a["name"], accent=a["accent_hex"])
        (PAGES_CSS / f"{slug}.css").write_text(css, encoding="utf-8")

        print(f"  generated /{slug}/")

    # Root index
    (ROOT / "index.html").write_text(render_index(advertisers), encoding="utf-8")
    print(f"  generated /index.html ({len(advertisers)} advertisers)")

if __name__ == "__main__":
    main()
