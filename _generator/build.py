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

def hero_img(slug: str) -> str:
    return f"https://picsum.photos/seed/{slug}-hero/2400/1400"

def gallery_img(slug: str, n: int) -> str:
    return f"https://picsum.photos/seed/{slug}-g{n}/900/900"

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

# ── Contact tiles + CTA helpers ─────────────────────────────────────────

def render_contact_tiles(adv: dict) -> str:
    tiles: list[str] = []
    if adv.get("phone"):
        tiles.append(f"""<a class="contact-tile" href="{tel_href(adv['phone'])}" aria-label="Call">{ICON_PHONE}<span class="contact-tile__label">Call</span></a>""")
    if adv.get("email"):
        tiles.append(f"""<a class="contact-tile" href="mailto:{adv['email']}" aria-label="Email">{ICON_EMAIL}<span class="contact-tile__label">Email</span></a>""")
    if adv.get("address"):
        tiles.append(f"""<a class="contact-tile" href="{directions_url(adv['name'], adv['address'])}" aria-label="Directions">{ICON_PIN_SMALL}<span class="contact-tile__label">Directions</span></a>""")
    if adv.get("instagram"):
        tiles.append(f"""<a class="contact-tile" href="{adv['instagram']}" aria-label="Instagram">{ICON_INSTAGRAM}<span class="contact-tile__label">Instagram</span></a>""")
    if adv.get("facebook"):
        tiles.append(f"""<a class="contact-tile" href="{adv['facebook']}" aria-label="Facebook">{ICON_FACEBOOK}<span class="contact-tile__label">Facebook</span></a>""")
    if adv.get("website"):
        tiles.append(f"""<a class="contact-tile" href="{adv['website']}" aria-label="Website">{ICON_WEBSITE}<span class="contact-tile__label">Website</span></a>""")
    return "\n      ".join(tiles)

def render_cta_block(adv: dict) -> str:
    buttons = []
    if adv.get("booking_url"):
        buttons.append(f'<a class="btn" href="{adv["booking_url"]}">Book</a>')
        if adv.get("website"):
            buttons.append(f'<a class="btn btn--ghost" href="{adv["website"]}">Visit website</a>')
    elif adv.get("website"):
        buttons.append(f'<a class="btn" href="{adv["website"]}">Visit website</a>')
    elif adv.get("address"):
        buttons.append(f'<a class="btn" href="{directions_url(adv["name"], adv["address"])}">Get directions</a>')
    if not buttons:
        return ""
    return f"""<!-- ─── Primary CTAs ───────────────────────────────────────────── -->
  <div class="cta-row">
    {chr(10).join('    ' + b for b in buttons).strip()}
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
  <link rel="stylesheet" href="/assets/css/pages/{slug}.css" />
</head>
<body>

  <!-- ─── Hero ───────────────────────────────────────────────────── -->
  <section class="hero">
    <header class="guide-bar">
      <a class="guide-bar__mark" href="/">Beachcomber Guide</a>
      <a href="/{group_slug}/" class="guide-bar__back">‹ {group_label}</a>
    </header>

    <picture class="hero__art" aria-hidden="true">
      <img src="{hero_image}" alt="" loading="eager" fetchpriority="high" />
    </picture>

    <div class="hero__inner">
      <div class="hero__tags rise rise--1">
        <span class="hero__tag">{icon_category}{category}</span>
        <span class="hero__tag">{icon_pin}{distance_label}</span>
      </div>
      <h1 class="rise rise--2">{hero_name_html}</h1>
      <p class="hero__sub rise rise--3">{hero_subtitle}</p>
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
    <span class="offer__label">For Beachcomber guests</span>
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
    <strong>You found us through The Beachcomber Guide.</strong>
    A curated companion to the Central Coast, placed in every room. <a href="/">See the full guide</a>.
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
</head>
<body>

  <!-- ─── Hotel hero ─────────────────────────────────────────────── -->
  <section class="hero">
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

  <!-- ─── Four category cards ───────────────────────────────────── -->
  <section class="cats">
    <header class="cats__head">
      <p class="eyebrow">The Guide</p>
      <h2>Your companion to the stay.</h2>
      <p>Hotel essentials, the best places to eat and drink, things to do beyond the gates, and the map to tie it all together.</p>
    </header>
    <div class="cats__grid">
      <a class="cat-card" href="/hotel/">
        <span class="cat-card__icon">{icon_bed}</span>
        <span class="cat-card__title">Hotel info</span>
        <span class="cat-card__desc">Check-in, dining, facilities and everything Beachcomber.</span>
      </a>
      <a class="cat-card" href="/eat-and-drink/">
        <span class="cat-card__icon">{icon_fork}</span>
        <span class="cat-card__title">Eat &amp; drink</span>
        <span class="cat-card__desc">Restaurants, bars and food makers within easy reach.</span>
      </a>
      <a class="cat-card" href="/things-to-do/">
        <span class="cat-card__icon">{icon_compass}</span>
        <span class="cat-card__title">Things to do</span>
        <span class="cat-card__desc">Experiences, tours and standout local stops.</span>
      </a>
      <a class="cat-card" href="/map/">
        <span class="cat-card__icon">{icon_map}</span>
        <span class="cat-card__title">Local map</span>
        <span class="cat-card__desc">See every recommendation on one interactive map.</span>
      </a>
    </div>
  </section>

  <footer class="guide-foot">
    <strong>The Beachcomber Guide.</strong>
    A curated companion to the hotel and the Central Coast around it.
  </footer>

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
</head>
<body>

  <section class="hero">
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
  <section class="description">
    <p class="eyebrow">The hotel</p>
    <h2>{description_headline}</h2>
    <p>{description_p1}</p>
    <p>{description_p2}</p>
    <p>{description_p3}</p>
  </section>

  <section class="amenities">
    <header class="amenities__head">
      <p class="eyebrow">Facilities</p>
      <h2>What's on site.</h2>
    </header>
    <ul class="amenities__list">
      {amenities_list}
    </ul>
    {check_block}
  </section>

  <section class="dining">
    <header class="dining__head">
      <p class="eyebrow">Eat at the hotel</p>
      <h2>Two ways to settle in.</h2>
      <p>Both venues are inside the hotel — no driving required.</p>
    </header>
    <div class="dining__grid">
      {dining_cards}
    </div>
  </section>

  {contacts_block}

  <footer class="guide-foot">
    <strong>You're already here.</strong>
    The Beachcomber Guide also covers the wider Central Coast — <a href="/">return to the guide</a>.
  </footer>

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
</head>
<body>

  <header class="page-head">
    <a class="page-head__mark" href="/">‹ The Beachcomber Guide</a>
    <p class="eyebrow">The Guide</p>
    <h1>{headline}</h1>
    <p class="page-head__sub">{intro}</p>
  </header>

  <section class="list">
    <div class="list__grid">
      {cards}
    </div>
  </section>

  <footer class="guide-foot">
    <strong>The Beachcomber Guide.</strong>
    A curated companion to the hotel and the Central Coast around it. <a href="/map/">See the map</a>.
  </footer>

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
</head>
<body>

  <header class="page-head">
    <a class="page-head__mark" href="/">‹ The Beachcomber Guide</a>
    <p class="eyebrow">Local Map</p>
    <h1>Every recommendation, in one place.</h1>
    <p class="page-head__sub">{intro}</p>
  </header>

  <div id="map" class="map" role="application" aria-label="Interactive map of guide recommendations"></div>

  <section class="map-legend">
    <span class="legend-pip legend-pip--hotel"></span> The Beachcomber Hotel
    <span class="legend-pip legend-pip--eat"></span> Eat &amp; drink
    <span class="legend-pip legend-pip--do"></span> Things to do
  </section>

  <footer class="guide-foot">
    <strong>The Beachcomber Guide.</strong>
    Tap any pin for details and a link to that listing.
  </footer>

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
    return PAGE_TEMPLATE.format(
        name=html.escape(a["name"]),
        meta_description=html.escape(a["hero_subtitle"]),
        slug=a["slug"],
        hero_image=hero_img(a["slug"]),
        group_slug=a["category_group"],
        group_label=GROUP_LABELS.get(a["category_group"], a["category_group"]),
        icon_category=ICON_CATEGORY,
        icon_pin=ICON_PIN,
        category=html.escape(a["category"]),
        distance_label=distance_label(a),
        hero_name_html=hero_name_html(a["name"]),
        hero_subtitle=html.escape(a["hero_subtitle"]),
        cta_block=render_cta_block(a),
        description_headline=html.escape(a["description_headline"]),
        description_p1=html.escape(a["description_p1"]),
        description_p2=html.escape(a["description_p2"]),
        offer_headline=html.escape(a["offer_headline"]),
        offer_body=html.escape(a["offer_body"]),
        offer_code=html.escape(a["offer_code"]),
        contacts_block=render_contacts_block(a),
        gallery_headline=html.escape(f"From {a['suburb']}."),
        g1=gallery_img(a["slug"], 1),
        g2=gallery_img(a["slug"], 2),
        g3=gallery_img(a["slug"], 3),
        g4=gallery_img(a["slug"], 4),
        g5=gallery_img(a["slug"], 5),
        g6=gallery_img(a["slug"], 6),
    )

def render_hotel_page(hotel: dict, on_site: list[dict]) -> str:
    return HOTEL_TEMPLATE.format(
        name=html.escape(hotel["name"]),
        meta_description=html.escape(hotel["hero_subtitle"]),
        hero_image=hero_img("beachcomber-hotel"),
        suburb=html.escape(hotel["suburb"]),
        hero_name_html=hero_name_html(hotel["name"]),
        hero_subtitle=html.escape(hotel["hero_subtitle"]),
        cta_block=render_cta_block(hotel),
        description_headline=html.escape(hotel["description_headline"]),
        description_p1=html.escape(hotel["description_p1"]),
        description_p2=html.escape(hotel["description_p2"]),
        description_p3=html.escape(hotel.get("description_p3", "")),
        amenities_list=render_amenities(hotel.get("amenities", [])),
        check_block=render_check_block(hotel),
        dining_cards="\n      ".join(render_dining_card(v) for v in on_site),
        contacts_block=render_contacts_block(hotel),
    )

def render_root(hotel: dict) -> str:
    return ROOT_TEMPLATE.format(
        hero_image=hero_img("beachcomber-hotel"),
        hotel_name_html=hero_name_html(hotel["name"]),
        hotel_hero_subtitle=html.escape(hotel["hero_subtitle"]),
        icon_bed=ICON_BED,
        icon_fork=ICON_FORK,
        icon_compass=ICON_COMPASS,
        icon_map=ICON_MAP,
    )

def render_category(group_slug: str, label: str, intro: str, advertisers: list[dict]) -> str:
    cards = [render_list_card(a) for a in sorted(advertisers, key=lambda x: x["distance_minutes"])]
    return CATEGORY_TEMPLATE.format(
        label=html.escape(label),
        meta_description=html.escape(intro),
        headline=html.escape(label + " — within easy reach."),
        intro=html.escape(intro),
        cards="\n      ".join(cards),
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
