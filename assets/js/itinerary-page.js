/* Itinerary page controller.

   Server-rendered shell; client populates the list from localStorage
   (or a ?stops=… shared URL). Renders the same venue-card shape used
   in the chat surface so guests see one consistent affordance. */

(function () {
  "use strict";

  const root = document.querySelector("[data-itin]");
  if (!root) return;

  const VENUES = (window.GUIDE && window.GUIDE.venues) || [];
  const venueBySlug = Object.create(null);
  VENUES.forEach(v => { venueBySlug[v.slug] = v; });

  const subEl = root.querySelector("[data-sub]");
  const sharedEl = root.querySelector("[data-shared]");
  const actionsEl = root.querySelector("[data-actions]");
  const emptyEl = root.querySelector("[data-empty]");
  const listEl = root.querySelector("[data-list]");
  const importBtn = root.querySelector("[data-import]");
  const shareBtn = root.querySelector("[data-share]");
  const clearBtn = root.querySelector("[data-clear]");
  const shareStatus = root.querySelector("[data-share-status]");

  /* ── Helpers ──────────────────────────────────────────────────── */

  function el(tag, cls, text) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function distanceLabel(v) {
    if (v.distance === 0) return v.suburb + " · At the hotel";
    return v.suburb + " · " + v.distance + " min from the hotel";
  }

  function directionsHref(v) {
    const q = (v.name + " " + (v.address || "")).trim();
    return "https://maps.google.com/?q=" + encodeURIComponent(q);
  }

  function venueCard(slug) {
    const v = venueBySlug[slug];
    if (!v) return null;

    const card = document.createElement("a");
    card.className = "venue-card";
    card.href = "/" + v.slug + "/";

    const media = el("div", "venue-card__media");
    const img = document.createElement("img");
    img.src = v.image; img.alt = ""; img.loading = "lazy"; img.decoding = "async";
    media.appendChild(img);

    const body = el("div", "venue-card__body");
    body.appendChild(el("span", "venue-card__cat", v.category));
    body.appendChild(el("h3", "venue-card__name", v.name));
    body.appendChild(el("p", "venue-card__meta", distanceLabel(v)));
    if (v.perk) body.appendChild(el("p", "venue-card__perk", v.perk));

    const actions = document.createElement("div");
    actions.className = "venue-card__actions";
    actions.appendChild(action("View page", "/" + v.slug + "/", "primary"));
    if (v.booking_url) actions.appendChild(action("Book", v.booking_url));
    actions.appendChild(action("Directions", directionsHref(v)));

    /* Remove button — separate, smaller affordance below the actions. */
    const remove = el("button", "venue-card__remove", "Remove");
    remove.type = "button";
    remove.setAttribute("data-remove", v.slug);
    remove.setAttribute("aria-label", "Remove " + v.name + " from itinerary");

    card.appendChild(media);
    card.appendChild(body);
    card.appendChild(actions);
    card.appendChild(remove);
    return card;
  }

  function action(label, href, variant) {
    const a = document.createElement("a");
    a.className = "venue-card__action" + (variant === "primary" ? " venue-card__action--primary" : "");
    a.href = href;
    a.textContent = label;
    a.addEventListener("click", (e) => e.stopPropagation());
    return a;
  }

  /* ── Mode: own itinerary vs shared preview ───────────────────── */

  function getMode() {
    const sharedSlugs = window.Itinerary.fromUrl();
    if (sharedSlugs.length) return { mode: "shared", slugs: sharedSlugs };
    return { mode: "own", slugs: window.Itinerary.get() };
  }

  function render() {
    const state = getMode();
    listEl.innerHTML = "";

    if (state.mode === "shared") {
      sharedEl.hidden = false;
      actionsEl.hidden = true;
      emptyEl.hidden = true;
      subEl.textContent = "Someone shared these stops with you.";
    } else {
      sharedEl.hidden = true;
      if (state.slugs.length === 0) {
        actionsEl.hidden = true;
        emptyEl.hidden = false;
        subEl.textContent = "What you've saved for the trip.";
        return;
      }
      actionsEl.hidden = false;
      emptyEl.hidden = true;
      const n = state.slugs.length;
      subEl.textContent = n + (n === 1 ? " stop saved." : " stops saved.");
    }

    state.slugs.forEach(slug => {
      const card = venueCard(slug);
      if (card) listEl.appendChild(card);
    });
  }

  /* ── Actions ─────────────────────────────────────────────────── */

  if (importBtn) {
    importBtn.addEventListener("click", () => {
      const shared = window.Itinerary.fromUrl();
      if (!shared.length) return;
      window.Itinerary.addMany(shared);
      /* Strip the query string so reloading shows the user's own list. */
      window.history.replaceState({}, "", "/itinerary/");
      render();
    });
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      if (!confirm("Clear all saved stops?")) return;
      window.Itinerary.clear();
    });
  }

  if (shareBtn) {
    shareBtn.addEventListener("click", async () => {
      const url = window.Itinerary.shareUrl();
      const title = "My Beachcomber itinerary";
      let messaged = false;
      if (navigator.share) {
        try {
          await navigator.share({ title: title, url: url });
          messaged = true;
        } catch (e) { /* user cancelled or unsupported */ }
      }
      if (!messaged) {
        try {
          await navigator.clipboard.writeText(url);
          shareStatus.textContent = "Link copied to clipboard.";
          shareStatus.hidden = false;
          setTimeout(() => { shareStatus.hidden = true; }, 2400);
        } catch (e) {
          shareStatus.textContent = url;
          shareStatus.hidden = false;
        }
      }
    });
  }

  /* Remove via event delegation. */
  listEl.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-remove]");
    if (!btn) return;
    e.preventDefault();
    const slug = btn.getAttribute("data-remove");
    window.Itinerary.remove(slug);
  });

  /* React to changes from any surface. */
  document.addEventListener("bg:itinerary-changed", render);

  /* ── Boot ────────────────────────────────────────────────────── */

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();
