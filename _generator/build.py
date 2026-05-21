#!/usr/bin/env python3
"""
The Guide — page generator for the Beachcomber Hotel.

Reads _generator/advertisers.json and produces:

  /index.html                       Hotel hero + four category cards
  /hotel/index.html                 Hotel info + on-site dining + amenities
  /eat-and-drink/index.html         Filtered list of eat-and-drink businesses
  /things-to-do/index.html          Filtered list of things-to-do businesses
  /map/index.html                   Local-area map (Leaflet + OSM tiles)
  /{slug}/index.html                One per business
  /assets/css/pages/{slug}.css      Per-business palette

Re-run after editing the JSON. The deployed site is fully static —
this script is a one-time scaffolder, not a deploy-time build step.
"""

import html
import json
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "_generator" / "advertisers.json"
PAGES_CSS = ROOT / "assets" / "css" / "pages"

# ── Helpers ──────────────────────────────────────────────────────────────

# ── Image library ──────────────────────────────────────────────────────
# Themed Unsplash photo IDs by category. Each business is mapped to a
# category in HERO_CATEGORY below. Gallery is six Central Coast shots
# rotated across every page so visuals stay coherent without dipping
# into stock-photo-fatigue territory.
UNSPLASH_IDS = {
    "mexican-cantina":   "photo-1565299585323-38d6b0865b47",
    "thai-massage":      "photo-1544161515-4ab6ce6db874",
    "beach-restaurant":  "photo-1455587734955-081b22074882",
    "music-bar":         "photo-1514933651103-005eec06c04b",
    "fashion-boutique":  "photo-1567401893414-76b7b1e5a7a5",
    "bbq-smokehouse":    "photo-1544025162-d76694265947",
    "boat-hire":         "photo-1502209524164-acea936639a2",
    "day-spa":           "photo-1540555700478-4be289fbecef",
    "dining-precinct":   "photo-1517248135467-4c7edcad34c4",
    "aero-club":         "photo-1436491865332-7a61a109cc05",
    "farm-park":         "photo-1500595046743-cd271d694d30",
    "alpaca-farm":       "photo-1452857297128-d9c29adba80b",
    "high-ropes":        "photo-1448375240586-882707db888b",
    "photo-gallery":     "photo-1577720580479-7d839d829c73",
    "gin-distillery":    "photo-1514362545857-3bc16c4c7d1b",
    "chocolate-factory": "photo-1481391319762-47dff72954d9",
    "reptile-park":      "photo-1504208434309-cb69f4fe52b0",
    "hat-shop":          "photo-1521369909029-2afed882baee",
    "pearl-oysters":     "photo-1611516491426-03025e6043c8",
    "hotel-restaurant":  "photo-1414235077428-338989a2e8c0",
    "bistro-bar":        "photo-1513104890138-7c749659a591",
    "waterfront-hotel":  "photo-1571896349842-33c89424de2d",
    # Gallery — Central Coast / coastal NSW
    "coast-1":           "photo-1507525428034-b723cf961d3e",
    "coast-2":           "photo-1505228395891-9a51e7e86bf6",
    "coast-3":           "photo-1441974231531-c6227db76b6e",
    "coast-4":           "photo-1506905925346-21bda4d32df4",
    "coast-5":           "photo-1542273917363-3b1817f69a2d",
    "coast-6":           "photo-1591608971362-f08b2a75731a",
}

# slug → category key in UNSPLASH_IDS for hero
HERO_CATEGORY = {
    "mexicoast-cantina":         "mexican-cantina",
    "mangkorn-massage":          "thai-massage",
    "dunes-by-dish":             "beach-restaurant",
    "the-savoy-bar-and-music":   "music-bar",
    "plain-janes-store":         "fashion-boutique",
    "cue-and-crew":              "bbq-smokehouse",
    "bateau-tuggerah":           "boat-hire",
    "wildfire-day-spa":          "day-spa",
    "wyong-milk-factory":        "dining-precinct",
    "central-coast-aero-club":   "aero-club",
    "amazement-farm-fun-park":   "farm-park",
    "iris-lodge-alpacas":        "alpaca-farm",
    "treetops-adventure":        "high-ropes",
    "ken-duncan-gallery":        "photo-gallery",
    "distillery-botanica":       "gin-distillery",
    "chocolate-factory-gosford": "chocolate-factory",
    "australian-reptile-park":   "reptile-park",
    "coastal-hatters":           "hat-shop",
    "broken-bay-pearl-farm":     "pearl-oysters",
    "pelicans-restaurant":       "hotel-restaurant",
    "beachie-bar-and-bistro":    "bistro-bar",
    "beachcomber":               "waterfront-hotel",
}

GALLERY_KEYS = ["coast-1", "coast-2", "coast-3", "coast-4", "coast-5", "coast-6"]

def _unsplash(key: str, w: int, h: int) -> str:
    """Construct an Unsplash CDN URL. The `images.unsplash.com` host is a
    long-running CDN and serves any well-formed photo ID at any size."""
    photo_id = UNSPLASH_IDS.get(key)
    if not photo_id:
        # Unknown category — fall back to a coast shot.
        photo_id = UNSPLASH_IDS["coast-1"]
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w={w}&q=80"

def hero_img(slug: str) -> str:
    return _unsplash(HERO_CATEGORY.get(slug, "coast-1"), 2400, 1400)

def gallery_img(slug: str, n: int) -> str:
    # n is 1-based (1..6). Rotate the start by hashing the slug so each
    # business shows the same six images in a different order.
    start = sum(ord(c) for c in slug) % len(GALLERY_KEYS)
    key = GALLERY_KEYS[(start + n - 1) % len(GALLERY_KEYS)]
    return _unsplash(key, 1200, 1200)

def tel_href(phone: str | None) -> str:
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

def distance_label(a: dict) -> str:
    d = a.get("distance_minutes", 0)
    if d == 0:
        return "At the hotel"
    return f"{d} min from the hotel"

# ── SVG icons ────────────────────────────────────────────────────────────

ICON_CATEGORY = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M4 12c2-4 5-6 8-6s6 2 8 6c-2 4-5 6-8 6s-6-2-8-6z"/></svg>"""
ICON_PIN = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 21s-7-7.5-7-12a7 7 0 0 1 14 0c0 4.5-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/></svg>"""
ICON_PHONE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true"><path d="M5 4h3l2 5-2.5 1.5a12 12 0 0 0 6 6L15 14l5 2v3a2 2 0 0 1-2 2A15 15 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>"""
ICON_EMAIL = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 7l9 6 9-6"/></svg>"""
ICON_PIN_SMALL = ICON_PIN
ICON_INSTAGRAM = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true"><rect x="3.5" y="3.5" width="17" height="17" rx="4.5"/><circle cx="12" cy="12" r="3.8"/><circle cx="17.3" cy="6.7" r="1" fill="currentColor" stroke="none"/></svg>"""
ICON_FACEBOOK = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true"><path d="M15 8h2.5V5H15a3.5 3.5 0 0 0-3.5 3.5V11H9v3h2.5v7h3v-7H17l.5-3h-3V8.5A.5.5 0 0 1 15 8z"/></svg>"""
ICON_WEBSITE = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/></svg>"""
ICON_BED = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M3 12V7a1 1 0 0 1 1-1h16a1 1 0 0 1 1 1v5"/><path d="M3 17v-3a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3"/><path d="M3 17v3M21 17v3"/><path d="M7 11V9a1 1 0 0 1 1-1h3a1 1 0 0 1 1 1v2"/></svg>"""
ICON_FORK = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M7 3v8a3 3 0 0 0 3 3h0v7"/><path d="M7 3v5M11 3v5"/><path d="M17 3v18M14 3h6v5a3 3 0 0 1-3 3"/></svg>"""
ICON_COMPASS = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M15.5 8.5l-2 5-5 2 2-5 5-2z" fill="currentColor" stroke="none"/></svg>"""
ICON_MAP = """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M3 6l6-2 6 2 6-2v14l-6 2-6-2-6 2V6z"/><path d="M9 4v16M15 6v16"/></svg>"""

# ── The dock (unified Claude prompt + nav) ─────────────────────────────

DOCK_MARK_SVG = (
    '<svg viewBox="0 0 24 24" aria-hidden="true">'
    '<path d="M12 2v8M12 14v8M2 12h8M14 12h8M4.93 4.93l5.66 5.66M13.41 13.41l5.66 5.66M4.93 19.07l5.66-5.66M13.41 10.59l5.66-5.66" '
    'stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/>'
    '</svg>'
)
DOCK_ARROW_SVG = (
    '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-linecap="round" stroke-linejoin="round" stroke-width="2" aria-hidden="true">'
    '<path d="M9 6l6 6-6 6"/></svg>'
)

def dock(active: str = "", initial_prompt: str = "Ask Claude about the guide") -> str:
    """Unified bottom dock — Claude prompt row on top, nav row beneath.
    `active` is one of: 'hotel', 'eat', 'do', 'map' (or '' for home)."""
    def item(href: str, key: str, label: str) -> str:
        ac = ' aria-current="page"' if active == key else ""
        return f'<a href="{href}"{ac}>{label}</a>'
    return f"""<!-- ─── Dock (Claude + nav) ────────────────────────────────────── -->
  <aside class="dock" aria-label="Guide controls">
    <div class="dock__inner">
      <button class="dock__claude" type="button" data-claude-open aria-label="Ask Claude">
        <span class="dock__claude-mark" aria-hidden="true">{DOCK_MARK_SVG}</span>
        <span class="dock__claude-prompt" data-bar-prompt>{html.escape(initial_prompt)}</span>
        <span class="dock__claude-arrow" aria-hidden="true">{DOCK_ARROW_SVG}</span>
      </button>
      <div class="dock__divider" aria-hidden="true"></div>
      <nav class="dock__nav" aria-label="Guide sections">
        {item('/hotel/', 'hotel', 'Hotel')}
        {item('/eat-and-drink/', 'eat', 'Eat')}
        {item('/things-to-do/', 'do', 'Do')}
        {item('/map/', 'map', 'Map')}
      </nav>
    </div>
  </aside>"""

# ── Visit row (text-only contact line) + CTA helpers ───────────────────

def render_visit_row(adv: dict) -> str:
    """Text-only row of contact + social links, separated by middle dots."""
    items: list[str] = []
    if adv.get("phone"):
        items.append(f'<a href="{tel_href(adv["phone"])}">Call</a>')
    if adv.get("email"):
        items.append(f'<a href="mailto:{adv["email"]}">Email</a>')
    if adv.get("address"):
        items.append(f'<a href="{directions_url(adv["name"], adv["address"])}">Directions</a>')
    if adv.get("website"):
        items.append(f'<a href="{adv["website"]}">Website</a>')
    if adv.get("instagram"):
        items.append(f'<a href="{adv["instagram"]}">Instagram</a>')
    if adv.get("facebook"):
        items.append(f'<a href="{adv["facebook"]}">Facebook</a>')
    if not items:
        return ""
    sep = '<span class="visit-row__sep" aria-hidden="true">·</span>'
    inner = sep.join(items)
    return (
        '<section class="visit-row" aria-label="Visit and contact" '
        'data-claude-section data-claude-topic="visit" '
        f'data-claude-name="{html.escape(adv["name"])}" '
        f'data-claude-prompt="Ask Claude about getting to {html.escape(adv["name"])}">'
        '\n    <span class="visit-row__label">Visit</span>\n    '
        + inner +
        "\n  </section>"
    )

def render_cta_block(adv: dict) -> str:
    """Single primary CTA where possible; ghost fallback for website."""
    buttons = []
    if adv.get("booking_url"):
        buttons.append(f'<a class="btn" href="{adv["booking_url"]}">Book</a>')
    elif adv.get("website"):
        buttons.append(f'<a class="btn" href="{adv["website"]}">Visit website</a>')
    elif adv.get("address"):
        buttons.append(f'<a class="btn" href="{directions_url(adv["name"], adv["address"])}">Get directions</a>')
    if not buttons:
        return ""
    return f"""<!-- ─── Primary CTA ────────────────────────────────────────────── -->
  <div class="cta-row">
    {buttons[0]}
  </div>
"""

# ── Business page template ──────────────────────────────────────────────

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>{name} — The Beachcomber Guide</title>
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
  <link rel="stylesheet" href="/assets/css/claude.css" />
  <link rel="stylesheet" href="/assets/css/pages/{slug}.css" />
</head>
<body>

  <!-- ─── Hero ───────────────────────────────────────────────────── -->
  <section class="hero"
           data-claude-section
           data-claude-topic="place"
           data-claude-name="{name}"
           data-claude-prompt="Ask Claude about {name}">
    <header class="guide-bar">
      <a class="guide-bar__mark" href="/">Beachcomber Guide</a>
      <a href="/{group_slug}/" class="guide-bar__back">‹ {group_label}</a>
    </header>

    <picture class="hero__art" aria-hidden="true">
      <img src="{hero_image}" alt="" loading="eager" fetchpriority="high" />
    </picture>

    <div class="hero__inner">
      <p class="hero__eyebrow rise rise--1">{suburb_line}</p>
      <h1 class="rise rise--2">{hero_name_html}</h1>
      <p class="hero__sub rise rise--3">{hero_subtitle}</p>
    </div>
  </section>

  {cta_block}

  <section class="description"
           data-claude-section
           data-claude-topic="place"
           data-claude-name="{name}"
           data-claude-prompt="Ask Claude about the experience at {name}">
    <h2>{description_headline}</h2>
    <p>{description_p1}</p>
    <p>{description_p2}</p>
  </section>

  <aside class="offer"
         aria-label="Offer for Guide readers"
         data-claude-section
         data-claude-topic="perk"
         data-claude-name="{name}"
         data-claude-prompt="Ask Claude how to redeem this perk">
    <span class="offer__label">Guest perk</span>
    <h3>{offer_headline}</h3>
    <p>{offer_body}</p>
    <span class="offer__code">{offer_code}</span>
  </aside>

  {visit_row}

  <section class="gallery-section"
           aria-label="Gallery"
           data-claude-section
           data-claude-topic="gallery"
           data-claude-name="{name}"
           data-claude-prompt="Ask Claude about visiting {name}">
    <div class="gallery">
      <figure class="gallery__tile"><img src="{g1}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g2}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g3}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g4}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g5}" alt="" loading="lazy" /></figure>
      <figure class="gallery__tile"><img src="{g6}" alt="" loading="lazy" /></figure>
    </div>
  </section>

  {dock}

  <script src="/assets/js/claude.js" defer></script>

</body>
</html>
"""

CSS_TEMPLATE = """/* {name} — per-advertiser palette. Generated from advertisers.json. */

:root {{
  --accent:     {accent};
  --accent-ink: #FFFFFF;
}}
"""

GROUP_LABELS = {
    "eat-and-drink": "Eat & Drink",
    "things-to-do": "Things to do",
}

# ── Root index template (Hotel hero + 4 category cards) ────────────────

ROOT_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>The Beachcomber Guide</title>
  <meta name="description" content="A curated companion to the Beachcomber Hotel and the Central Coast — what to do, where to eat, and the map to get you there." />
  <meta name="theme-color" content="#FFFFFF" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="preconnect" href="https://picsum.photos" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />

  <link rel="stylesheet" href="/assets/css/tokens.css" />
  <link rel="stylesheet" href="/assets/css/guide.css" />
  <link rel="stylesheet" href="/assets/css/claude.css" />
</head>
<body>

  <!-- ─── Hotel hero ─────────────────────────────────────────────── -->
  <section class="hero"
           data-claude-section
           data-claude-topic="hotel"
           data-claude-prompt="Ask Claude about the hotel">
    <header class="guide-bar">
      <a class="guide-bar__mark" href="/">The Beachcomber Guide</a>
      <span>Central Coast</span>
    </header>

    <picture class="hero__art" aria-hidden="true">
      <img src="{hero_image}" alt="" loading="eager" fetchpriority="high" />
    </picture>

    <div class="hero__inner">
      <p class="hero__eyebrow rise rise--1">Welcome to the Coast</p>
      <h1 class="rise rise--2">{hotel_name_html}</h1>
      <p class="hero__sub rise rise--3">{hotel_hero_subtitle}</p>
    </div>
  </section>

  <section class="cats"
           data-claude-section
           data-claude-topic="guide"
           data-claude-prompt="Ask Claude what to do today">
    <header class="cats__head">
      <h2>Your companion to the stay.</h2>
    </header>
    <div class="cats__grid">
      <a class="cat-card" href="/hotel/">
        <img class="cat-card__img" src="{cat_img_hotel}" alt="" loading="lazy" />
        <div class="cat-card__body">
          <span class="cat-card__title">Hotel info</span>
          <span class="cat-card__desc">Check-in, dining, facilities and everything Beachcomber.</span>
        </div>
      </a>
      <a class="cat-card" href="/eat-and-drink/">
        <img class="cat-card__img" src="{cat_img_eat}" alt="" loading="lazy" />
        <div class="cat-card__body">
          <span class="cat-card__title">Eat &amp; drink</span>
          <span class="cat-card__desc">Restaurants, bars and food makers within easy reach.</span>
        </div>
      </a>
      <a class="cat-card" href="/things-to-do/">
        <img class="cat-card__img" src="{cat_img_do}" alt="" loading="lazy" />
        <div class="cat-card__body">
          <span class="cat-card__title">Things to do</span>
          <span class="cat-card__desc">Experiences, tours and standout local stops.</span>
        </div>
      </a>
      <a class="cat-card" href="/map/">
        <img class="cat-card__img" src="{cat_img_map}" alt="" loading="lazy" />
        <div class="cat-card__body">
          <span class="cat-card__title">Local map</span>
          <span class="cat-card__desc">See every recommendation on one interactive map.</span>
        </div>
      </a>
    </div>
  </section>

  {dock}

  <script src="/assets/js/claude.js" defer></script>

</body>
</html>
"""

# ── Hotel page template ────────────────────────────────────────────────

HOTEL_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>{name} — The Beachcomber Guide</title>
  <meta name="description" content="{meta_description}" />
  <meta name="theme-color" content="#FFFFFF" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="preconnect" href="https://picsum.photos" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />

  <link rel="stylesheet" href="/assets/css/tokens.css" />
  <link rel="stylesheet" href="/assets/css/guide.css" />
  <link rel="stylesheet" href="/assets/css/claude.css" />
</head>
<body>

  <section class="hero"
           data-claude-section
           data-claude-topic="hotel"
           data-claude-prompt="Ask Claude about the hotel">
    <header class="guide-bar">
      <a class="guide-bar__mark" href="/">Beachcomber Guide</a>
      <a href="/" class="guide-bar__back">‹ Home</a>
    </header>

    <picture class="hero__art" aria-hidden="true">
      <img src="{hero_image}" alt="" loading="eager" fetchpriority="high" />
    </picture>

    <div class="hero__inner">
      <p class="hero__eyebrow rise rise--1">{suburb}, Central Coast</p>
      <h1 class="rise rise--2">{hero_name_html}</h1>
      <p class="hero__sub rise rise--3">{hero_subtitle}</p>
    </div>
  </section>

  {cta_block}

  <section class="description"
           data-claude-section
           data-claude-topic="hotel"
           data-claude-prompt="Ask Claude about your stay">
    <h2>{description_headline}</h2>
    <p>{description_p1}</p>
    <p>{description_p2}</p>
    <p>{description_p3}</p>
  </section>

  <section class="amenities"
           data-claude-section
           data-claude-topic="facilities"
           data-claude-prompt="Ask Claude about hotel facilities">
    <header class="amenities__head">
      <h2>What's on site.</h2>
    </header>
    <ul class="amenities__list">
      {amenities_list}
    </ul>
    {check_block}
  </section>

  <section class="dining"
           data-claude-section
           data-claude-topic="dining"
           data-claude-prompt="Ask Claude what's open tonight">
    <header class="dining__head">
      <h2>Two ways to settle in.</h2>
      <p>Both venues are inside the hotel — no driving required.</p>
    </header>
    <div class="dining__grid">
      {dining_cards}
    </div>
  </section>

  {visit_row}

  {dock}

  <script src="/assets/js/claude.js" defer></script>

</body>
</html>
"""

# ── Category list template ─────────────────────────────────────────────

CATEGORY_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>{label} — The Beachcomber Guide</title>
  <meta name="description" content="{meta_description}" />
  <meta name="theme-color" content="#FFFFFF" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="preconnect" href="https://picsum.photos" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />

  <link rel="stylesheet" href="/assets/css/tokens.css" />
  <link rel="stylesheet" href="/assets/css/guide.css" />
  <link rel="stylesheet" href="/assets/css/claude.css" />
</head>
<body>

  <header class="app-bar">
    <a class="app-bar__mark" href="/">The Beachcomber Guide</a>
  </header>

  <header class="page-head"
          data-claude-section
          data-claude-topic="{topic}"
          data-claude-prompt="{bar_prompt}">
    <h1>{headline}</h1>
    <p class="page-head__sub">{intro}</p>
  </header>

  <section class="list"
           data-claude-section
           data-claude-topic="{topic}"
           data-claude-prompt="{list_prompt}">
    <div class="list__grid">
      {cards}
    </div>
  </section>

  {dock}

  <script src="/assets/js/claude.js" defer></script>

</body>
</html>
"""

# ── Map page template ──────────────────────────────────────────────────

MAP_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>Local map — The Beachcomber Guide</title>
  <meta name="description" content="Every Beachcomber Guide recommendation on one map of the Central Coast." />
  <meta name="theme-color" content="#FFFFFF" />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />

  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
  <link rel="stylesheet" href="/assets/css/tokens.css" />
  <link rel="stylesheet" href="/assets/css/guide.css" />
  <link rel="stylesheet" href="/assets/css/claude.css" />
</head>
<body>

  <header class="app-bar">
    <a class="app-bar__mark" href="/">The Beachcomber Guide</a>
  </header>

  <header class="page-head"
          data-claude-section
          data-claude-topic="map"
          data-claude-prompt="Ask Claude to plan a route">
    <h1>Every recommendation, in one place.</h1>
    <p class="page-head__sub">{intro}</p>
  </header>

  <div id="map" class="map"
       role="application"
       aria-label="Interactive map of guide recommendations"
       data-claude-section
       data-claude-topic="map"
       data-claude-prompt="Ask Claude what's closest"></div>

  <section class="map-legend">
    <span class="legend-pip legend-pip--hotel"></span> The Beachcomber Hotel
    <span class="legend-pip legend-pip--eat"></span> Eat &amp; drink
    <span class="legend-pip legend-pip--do"></span> Things to do
  </section>

  {dock}

  <script src="/assets/js/claude.js" defer></script>

  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
  <script>
    const HOTEL = {hotel_js};
    const SPOTS = {spots_js};

    const map = L.map('map', {{ scrollWheelZoom: true, zoomControl: true }});

    L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }}).addTo(map);

    function pinIcon(kind) {{
      const colour = kind === 'hotel' ? '#111113' : (kind === 'eat' ? '#B0451F' : '#1F4D3F');
      return L.divIcon({{
        className: 'map-pin map-pin--' + kind,
        html: '<span class="map-pin__dot" style="background:' + colour + '"></span>',
        iconSize: [22, 22],
        iconAnchor: [11, 11],
        popupAnchor: [0, -10],
      }});
    }}

    const hotelMarker = L.marker([HOTEL.lat, HOTEL.lng], {{ icon: pinIcon('hotel') }}).addTo(map);
    hotelMarker.bindPopup('<div class="map-pop"><span class="map-pop__cat">The Hotel</span><strong>' + HOTEL.name + '</strong><a href="/hotel/">View hotel info ›</a></div>');

    const bounds = [[HOTEL.lat, HOTEL.lng]];

    SPOTS.forEach(s => {{
      const kind = s.group === 'eat-and-drink' ? 'eat' : 'do';
      const m = L.marker([s.lat, s.lng], {{ icon: pinIcon(kind) }}).addTo(map);
      m.bindPopup(
        '<div class="map-pop">' +
        '<span class="map-pop__cat">' + s.category + '</span>' +
        '<strong>' + s.name + '</strong>' +
        '<span class="map-pop__meta">' + s.suburb + ' · ' + s.distance + ' min</span>' +
        '<a href="/' + s.slug + '/">Open page ›</a>' +
        '</div>'
      );
      bounds.push([s.lat, s.lng]);
    }});

    map.fitBounds(bounds, {{ padding: [40, 40] }});
  </script>

</body>
</html>
"""

# ── Rendering helpers for high-level pages ──────────────────────────────

def render_amenities(amenities: list[str]) -> str:
    return "\n      ".join(f"<li>{html.escape(a)}</li>" for a in amenities)

def render_check_block(hotel: dict) -> str:
    ci = hotel.get("check_in")
    co = hotel.get("check_out")
    if not ci and not co:
        return ""
    rows = []
    if ci:
        rows.append(f'<div><dt>Check in</dt><dd>{html.escape(ci)}</dd></div>')
    if co:
        rows.append(f'<div><dt>Check out</dt><dd>{html.escape(co)}</dd></div>')
    return f'<dl class="amenities__check">{"".join(rows)}</dl>'

def render_dining_card(venue: dict) -> str:
    return f"""<a class="dining-card" href="/{venue['slug']}/">
        <figure class="dining-card__media">
          <img src="{hero_img(venue['slug'])}" alt="" loading="lazy" />
        </figure>
        <div class="dining-card__body">
          <span class="dining-card__cat">{html.escape(venue.get('category', 'On-site dining'))}</span>
          <h3>{html.escape(venue['name'])}</h3>
          <p>{html.escape(venue.get('hero_subtitle', ''))}</p>
          <span class="dining-card__cta">See more ›</span>
        </div>
      </a>"""

def render_list_card(adv: dict) -> str:
    if adv["distance_minutes"] == 0:
        meta = f"{html.escape(adv['suburb'])} · At the hotel"
    else:
        meta = f"{html.escape(adv['suburb'])} · {adv['distance_minutes']} min from the hotel"
    return f"""<a class="list-card" href="/{adv['slug']}/">
        <figure class="list-card__media">
          <img src="{hero_img(adv['slug'])}" alt="" loading="lazy" />
        </figure>
        <div class="list-card__body">
          <span class="list-card__cat">{html.escape(adv['category'])}</span>
          <h3>{html.escape(adv['name'])}</h3>
          <p class="list-card__meta">{meta}</p>
        </div>
      </a>"""

def render_business_page(a: dict, hotel: dict) -> str:
    name = a["name"]
    group = a["category_group"]
    suburb_line = f"{a['suburb']} · {distance_label(a)}" if a.get("suburb") else distance_label(a)
    active = "eat" if group == "eat-and-drink" else ("do" if group == "things-to-do" else "")
    return PAGE_TEMPLATE.format(
        name=html.escape(name),
        meta_description=html.escape(a["hero_subtitle"]),
        slug=a["slug"],
        hero_image=hero_img(a["slug"]),
        group_slug=group,
        group_label=GROUP_LABELS.get(group, group),
        suburb_line=html.escape(suburb_line),
        hero_name_html=hero_name_html(name),
        hero_subtitle=html.escape(a["hero_subtitle"]),
        cta_block=render_cta_block(a),
        description_headline=html.escape(a["description_headline"]),
        description_p1=html.escape(a["description_p1"]),
        description_p2=html.escape(a["description_p2"]),
        offer_headline=html.escape(a["offer_headline"]),
        offer_body=html.escape(a["offer_body"]),
        offer_code=html.escape(a["offer_code"]),
        visit_row=render_visit_row(a),
        g1=gallery_img(a["slug"], 1),
        g2=gallery_img(a["slug"], 2),
        g3=gallery_img(a["slug"], 3),
        g4=gallery_img(a["slug"], 4),
        g5=gallery_img(a["slug"], 5),
        g6=gallery_img(a["slug"], 6),
        dock=dock(active),
    )

def render_hotel_page(hotel: dict, on_site: list[dict]) -> str:
    name = hotel["name"]
    return HOTEL_TEMPLATE.format(
        name=html.escape(name),
        meta_description=html.escape(hotel["hero_subtitle"]),
        hero_image=hero_img("beachcomber-hotel"),
        suburb=html.escape(hotel["suburb"]),
        hero_name_html=hero_name_html(name),
        hero_subtitle=html.escape(hotel["hero_subtitle"]),
        cta_block=render_cta_block(hotel),
        description_headline=html.escape(hotel["description_headline"]),
        description_p1=html.escape(hotel["description_p1"]),
        description_p2=html.escape(hotel["description_p2"]),
        description_p3=html.escape(hotel.get("description_p3", "")),
        amenities_list=render_amenities(hotel.get("amenities", [])),
        check_block=render_check_block(hotel),
        dining_cards="\n      ".join(render_dining_card(v) for v in on_site),
        visit_row=render_visit_row(hotel),
        dock=dock("hotel"),
    )

def render_root(hotel: dict) -> str:
    return ROOT_TEMPLATE.format(
        hero_image=hero_img("beachcomber-hotel"),
        hotel_name_html=hero_name_html(hotel["name"]),
        hotel_hero_subtitle=html.escape(hotel["hero_subtitle"]),
        cat_img_hotel=_unsplash("waterfront-hotel", 900, 1100),
        cat_img_eat=_unsplash("beach-restaurant", 900, 1100),
        cat_img_do=_unsplash("boat-hire", 900, 1100),
        cat_img_map=_unsplash("coast-1", 900, 1100),
        dock=dock(""),
    )

def render_category(group_slug: str, label: str, intro: str, advertisers: list[dict]) -> str:
    cards = [render_list_card(a) for a in sorted(advertisers, key=lambda x: x["distance_minutes"])]
    topic = "eat-listings" if group_slug == "eat-and-drink" else "do-listings"
    if group_slug == "eat-and-drink":
        bar_prompt = "Ask Claude where to eat tonight"
        list_prompt = "Ask Claude to pick one for you"
    else:
        bar_prompt = "Ask Claude what to do today"
        list_prompt = "Ask Claude to narrow this down"
    return CATEGORY_TEMPLATE.format(
        label=html.escape(label),
        meta_description=html.escape(intro),
        headline=html.escape(label + " — within easy reach."),
        intro=html.escape(intro),
        cards="\n      ".join(cards),
        topic=html.escape(topic),
        bar_prompt=html.escape(bar_prompt),
        list_prompt=html.escape(list_prompt),
        dock=dock("eat" if group_slug == "eat-and-drink" else "do"),
    )

def render_map(hotel: dict, advertisers: list[dict]) -> str:
    hotel_js = json.dumps({
        "name": hotel["name"],
        "lat": hotel["lat"],
        "lng": hotel["lng"],
    })
    spots = [
        {
            "slug": a["slug"], "name": a["name"], "category": a["category"],
            "suburb": a["suburb"], "distance": a["distance_minutes"],
            "lat": a["lat"], "lng": a["lng"], "group": a["category_group"],
        }
        for a in advertisers
        if a.get("lat") is not None and a.get("lng") is not None
    ]
    spots_js = json.dumps(spots)
    return MAP_TEMPLATE.format(
        intro="Tap any pin for the listing, distance and a link to the page.",
        hotel_js=hotel_js,
        spots_js=spots_js,
        dock=dock("map"),
    )

# ── Main ────────────────────────────────────────────────────────────────

def main() -> None:
    with open(DATA, "r", encoding="utf-8") as f:
        data = json.load(f)

    hotel = data["hotel"]
    advertisers = data["advertisers"]

    PAGES_CSS.mkdir(parents=True, exist_ok=True)

    # Per-business pages
    for a in advertisers:
        slug = a["slug"]
        page_dir = ROOT / slug
        page_dir.mkdir(parents=True, exist_ok=True)
        (page_dir / "index.html").write_text(render_business_page(a, hotel), encoding="utf-8")
        css = CSS_TEMPLATE.format(name=a["name"], accent=a["accent_hex"])
        (PAGES_CSS / f"{slug}.css").write_text(css, encoding="utf-8")
        print(f"  generated /{slug}/")

    # Hotel page (uses Pelicans + Beachie as on-site dining cards)
    on_site = [a for a in advertisers if a["slug"] in ("pelicans-restaurant", "beachie-bar-and-bistro")]
    (ROOT / "hotel").mkdir(parents=True, exist_ok=True)
    (ROOT / "hotel" / "index.html").write_text(render_hotel_page(hotel, on_site), encoding="utf-8")
    print("  generated /hotel/")

    # Category pages
    for group_slug, label, intro in [
        ("eat-and-drink", "Eat & Drink",
         "From the on-site bar and bistro to long lunches by the water — every place we'd send a guest, by drive time from the hotel."),
        ("things-to-do", "Things to do",
         "Walks, wildlife, workshops and the local stops worth the drive — every recommendation, by drive time from the hotel."),
    ]:
        in_group = [a for a in advertisers if a.get("category_group") == group_slug]
        (ROOT / group_slug).mkdir(parents=True, exist_ok=True)
        (ROOT / group_slug / "index.html").write_text(render_category(group_slug, label, intro, in_group), encoding="utf-8")
        print(f"  generated /{group_slug}/ ({len(in_group)} listings)")

    # Map page
    (ROOT / "map").mkdir(parents=True, exist_ok=True)
    (ROOT / "map" / "index.html").write_text(render_map(hotel, advertisers), encoding="utf-8")
    print(f"  generated /map/ ({len(advertisers) + 1} pins)")

    # Root index
    (ROOT / "index.html").write_text(render_root(hotel), encoding="utf-8")
    print("  generated /index.html")

if __name__ == "__main__":
    main()
