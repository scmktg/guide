/* Itinerary — the guest's saved-venues list.

   Loaded on every page. Owns:
   - localStorage persistence ({slugs:[...], updated_at:ms})
   - the topbar count badge that ticks up/down as venues are saved
   - shared URLs (?stops=slug1,slug2 — read on /itinerary/, applied on demand)
   - "Save" toggle buttons on venue pages and inside the chat surface
   - a single bg:itinerary-changed CustomEvent dispatched on the document
     so other surfaces (chat, badge) can react

   The storage is intentionally simple: an ordered list of slugs. Order
   reflects add-order — drive-time grouping and time-of-day buckets
   are a later concern. */

(function () {
  "use strict";

  const KEY = "bg.itinerary.v1";

  /* ── Storage ─────────────────────────────────────────────────── */

  function read() {
    try {
      const raw = localStorage.getItem(KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.slugs)) return [];
      return parsed.slugs.filter(s => typeof s === "string");
    } catch (e) { return []; }
  }

  function write(slugs) {
    try {
      localStorage.setItem(KEY, JSON.stringify({
        slugs: slugs,
        updated_at: Date.now()
      }));
    } catch (e) {}
  }

  function announce() {
    document.dispatchEvent(new CustomEvent("bg:itinerary-changed", {
      detail: { slugs: read() }
    }));
  }

  const Itinerary = {
    get: read,

    has(slug) {
      return read().indexOf(slug) !== -1;
    },

    add(slug) {
      const cur = read();
      if (cur.indexOf(slug) !== -1) return false;
      cur.push(slug);
      write(cur);
      announce();
      return true;
    },

    addMany(slugs) {
      const cur = read();
      let changed = false;
      slugs.forEach(s => {
        if (cur.indexOf(s) === -1) { cur.push(s); changed = true; }
      });
      if (changed) { write(cur); announce(); }
      return changed;
    },

    remove(slug) {
      const cur = read();
      const i = cur.indexOf(slug);
      if (i === -1) return false;
      cur.splice(i, 1);
      write(cur);
      announce();
      return true;
    },

    toggle(slug) {
      return this.has(slug) ? (this.remove(slug), false) : (this.add(slug), true);
    },

    set(slugs) {
      write(slugs.filter(s => typeof s === "string"));
      announce();
    },

    clear() {
      write([]);
      announce();
    },

    /* Read a comma-separated slug list from the URL (?stops=a,b,c). */
    fromUrl() {
      const p = new URLSearchParams(window.location.search);
      const raw = p.get("stops");
      if (!raw) return [];
      return raw.split(",").map(s => s.trim()).filter(Boolean);
    },

    /* Build a shareable URL for the current itinerary. */
    shareUrl() {
      const slugs = read();
      const u = new URL(window.location.origin + "/itinerary/");
      if (slugs.length) u.searchParams.set("stops", slugs.join(","));
      return u.toString();
    }
  };

  window.Itinerary = Itinerary;

  /* ── Topbar count badge ──────────────────────────────────────── */

  function syncBadges() {
    const n = read().length;
    document.querySelectorAll("[data-itinerary-count]").forEach(el => {
      el.textContent = String(n);
      el.hidden = n === 0;
    });
  }

  /* React when storage changes (same tab via announce, or another tab
     via the browser storage event). */
  document.addEventListener("bg:itinerary-changed", syncBadges);
  window.addEventListener("storage", (e) => {
    if (e.key === KEY) syncBadges();
  });

  /* ── Save toggle buttons (delegated, works for any [data-save-toggle]
        rendered on the page or injected later) ────────────────────── */

  function syncToggle(btn) {
    const slug = btn.getAttribute("data-save-toggle");
    if (!slug) return;
    const saved = Itinerary.has(slug);
    btn.setAttribute("aria-pressed", saved ? "true" : "false");
    btn.classList.toggle("is-saved", saved);
    const labelEl = btn.querySelector("[data-save-label]");
    if (labelEl) labelEl.textContent = saved ? "Saved" : "Save";
  }

  function syncAllToggles() {
    document.querySelectorAll("[data-save-toggle]").forEach(syncToggle);
  }

  document.addEventListener("bg:itinerary-changed", syncAllToggles);

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-save-toggle]");
    if (!btn) return;
    e.preventDefault();
    const slug = btn.getAttribute("data-save-toggle");
    if (!slug) return;
    Itinerary.toggle(slug);
    /* syncAllToggles fires automatically via the change event. */
  });

  /* ── "Save these to my itinerary" — bulk button (used in chat for
        multi-venue replies) ───────────────────────────────────────── */

  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-save-many]");
    if (!btn) return;
    e.preventDefault();
    const raw = btn.getAttribute("data-save-many") || "";
    const slugs = raw.split(",").map(s => s.trim()).filter(Boolean);
    if (!slugs.length) return;
    const added = Itinerary.addMany(slugs);
    /* Inline confirmation: swap the label and disable further clicks. */
    btn.disabled = true;
    btn.classList.add("is-saved");
    const labelEl = btn.querySelector("[data-save-many-label]");
    const newLabel = added ? "Saved to your itinerary" : "Already in your itinerary";
    if (labelEl) labelEl.textContent = newLabel;
    else btn.textContent = newLabel;
  });

  /* ── Topbar transparent → solid on scroll ─────────────────────
     Pages with a hero photo (topbar--fixed) start with a translucent
     topbar over the photo and turn solid as the user scrolls past the
     hero. Pages without a hero ship with topbar--solid baked in. */

  function initTopbar() {
    const topbar = document.querySelector(".topbar");
    if (!topbar) return;
    if (topbar.classList.contains("topbar--solid")) return;
    const hero = document.querySelector(".hero");
    if (!hero) {
      topbar.classList.add("is-solid");
      return;
    }
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          topbar.classList.toggle("is-solid", !e.isIntersecting);
        });
      },
      { rootMargin: "-50px 0px 0px 0px" }
    );
    obs.observe(hero);
  }

  /* ── Boot ────────────────────────────────────────────────────── */

  function boot() {
    syncBadges();
    syncAllToggles();
    initTopbar();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
