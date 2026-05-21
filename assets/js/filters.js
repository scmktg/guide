/* Opening hours + filters.

   This script does three jobs:

   1. Reads `data-hours` (a JSON map of weekday → intervals) from any
      element with `[data-status-pill]` inside it, works out whether
      the place is open right now in Sydney time, and renders a small
      Open / Closed / Hours-by-appt pill into that slot.

   2. On category pages (eat-and-drink, things-to-do), wires up the
      filter button in the topbar to open a bottom-sheet panel with
      an "Open now" toggle + drive-time chips. Toggling either
      filter hides/shows list cards.

   3. On business pages, also expands `[data-hours-table]` into a
      pretty weekly schedule with today highlighted. */

(function () {
  "use strict";

  const DAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"];
  const DAY_LABELS = {
    mon: "Mon", tue: "Tue", wed: "Wed", thu: "Thu",
    fri: "Fri", sat: "Sat", sun: "Sun"
  };
  const DAY_FULL = {
    mon: "Monday", tue: "Tuesday", wed: "Wednesday", thu: "Thursday",
    fri: "Friday", sat: "Saturday", sun: "Sunday"
  };

  /* ── Time in Sydney ──────────────────────────────────────────────── */

  function sydneyNow() {
    /* Use Intl to grab the current Sydney weekday + HH:MM regardless
       of the user's local timezone. */
    const fmt = new Intl.DateTimeFormat("en-US", {
      timeZone: "Australia/Sydney",
      weekday: "short",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false
    });
    const parts = Object.fromEntries(
      fmt.formatToParts(new Date()).map((p) => [p.type, p.value])
    );
    const day = parts.weekday.toLowerCase().slice(0, 3);
    let hh = parseInt(parts.hour, 10);
    if (parts.hour === "24") hh = 0;
    const mm = parseInt(parts.minute, 10);
    return { day, minutes: hh * 60 + mm };
  }

  function parseHM(s) {
    const [h, m] = s.split(":").map(Number);
    return h * 60 + m;
  }

  function fmtHM(s) {
    /* "09:00" → "9 am", "17:30" → "5:30 pm". */
    const [h, m] = s.split(":").map(Number);
    const ampm = h >= 12 ? "pm" : "am";
    const h12 = h % 12 === 0 ? 12 : h % 12;
    return m === 0 ? `${h12} ${ampm}` : `${h12}:${String(m).padStart(2, "0")} ${ampm}`;
  }

  function intervalsFor(hours, day) {
    if (!hours || !hours[day]) return [];
    return hours[day];
  }

  function isOpenAt(hours, now) {
    const intervals = intervalsFor(hours, now.day);
    return intervals.some(([open, close]) => {
      return now.minutes >= parseHM(open) && now.minutes < parseHM(close);
    });
  }

  function hasAnyHours(hours) {
    if (!hours) return false;
    return DAYS.some((d) => (hours[d] || []).length > 0);
  }

  /* ── Pills ──────────────────────────────────────────────────────── */

  function renderPill(el, hours, now) {
    if (!hasAnyHours(hours)) {
      el.className = "status status--unknown";
      el.textContent = "By appointment";
      return;
    }
    if (isOpenAt(hours, now)) {
      el.className = "status status--open";
      el.textContent = "Open now";
      return;
    }
    el.className = "status status--closed";
    el.textContent = "Closed";
  }

  function readHours(el) {
    /* Hours live on the card (eg. <a class="list-card" data-hours='{}'>),
       which is the parent or ancestor of the pill slot. */
    const host = el.closest("[data-hours]") || el;
    try {
      return JSON.parse(host.getAttribute("data-hours") || "null");
    } catch {
      return null;
    }
  }

  function readDistance(el) {
    const host = el.closest("[data-distance]") || el;
    const v = host.getAttribute("data-distance");
    return v == null ? null : parseFloat(v);
  }

  function renderAllPills(now) {
    document.querySelectorAll("[data-status-pill]").forEach((el) => {
      renderPill(el, readHours(el), now);
    });
  }

  /* ── Weekly schedule table (business pages) ──────────────────────── */

  function renderHoursTable(now) {
    document.querySelectorAll("[data-hours-table]").forEach((el) => {
      const host = el.closest("[data-hours]") || el;
      let hours = null;
      try { hours = JSON.parse(host.getAttribute("data-hours") || "null"); }
      catch { hours = null; }

      if (!hasAnyHours(hours)) {
        el.innerHTML = '<p class="hours__none">Hours are by appointment — get in touch to arrange a visit.</p>';
        return;
      }

      const rows = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"].map((d) => {
        const intervals = intervalsFor(hours, d);
        const label = intervals.length
          ? intervals.map(([o, c]) => `${fmtHM(o)} – ${fmtHM(c)}`).join(", ")
          : "Closed";
        const today = d === now.day ? " hours__row--today" : "";
        const closed = intervals.length ? "" : " hours__row--closed";
        return (
          `<div class="hours__row${today}${closed}">` +
          `<dt>${DAY_FULL[d]}</dt><dd>${label}</dd>` +
          `</div>`
        );
      }).join("");
      el.innerHTML = '<dl class="hours__grid">' + rows + "</dl>";
    });
  }

  /* ── Filter sheet (category pages) ──────────────────────────────── */

  function buildFilterSheet() {
    const sheet = document.createElement("div");
    sheet.className = "filter-sheet";
    sheet.setAttribute("role", "dialog");
    sheet.setAttribute("aria-modal", "true");
    sheet.setAttribute("aria-labelledby", "filter-sheet-title");
    sheet.innerHTML =
      '<div class="filter-sheet__scrim" data-close></div>' +
      '<div class="filter-sheet__panel">' +
        '<header class="filter-sheet__head">' +
          '<h2 id="filter-sheet-title">Filter</h2>' +
          '<button class="filter-sheet__close" data-close aria-label="Close">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">' +
              '<path d="M6 6l12 12M18 6L6 18"/></svg>' +
          '</button>' +
        '</header>' +

        '<div class="filter-sheet__body">' +
          '<section class="filter-row">' +
            '<div class="filter-row__copy">' +
              '<h3 class="filter-row__title">Open now</h3>' +
              '<p class="filter-row__sub">Only show places open right now.</p>' +
            '</div>' +
            '<label class="switch">' +
              '<input type="checkbox" data-filter-open />' +
              '<span class="switch__track"><span class="switch__thumb"></span></span>' +
            '</label>' +
          '</section>' +

          '<section class="filter-row filter-row--column">' +
            '<div class="filter-row__copy">' +
              '<h3 class="filter-row__title">Drive time from the hotel</h3>' +
              '<p class="filter-row__sub">Filter by how far places are.</p>' +
            '</div>' +
            '<div class="filter-row__chips" role="tablist">' +
              '<button class="chip is-active" data-distance="any" aria-pressed="true">Any</button>' +
              '<button class="chip" data-distance="15" aria-pressed="false">≤ 15 min</button>' +
              '<button class="chip" data-distance="30" aria-pressed="false">≤ 30 min</button>' +
              '<button class="chip" data-distance="60" aria-pressed="false">≤ 60 min</button>' +
            '</div>' +
          '</section>' +
        '</div>' +

        '<footer class="filter-sheet__foot">' +
          '<button class="filter-sheet__reset" type="button" data-filter-reset>Reset</button>' +
          '<span class="filter-sheet__count" data-filter-count></span>' +
          '<button class="filter-sheet__apply" type="button" data-close>Show results</button>' +
        '</footer>' +
      '</div>';
    document.body.appendChild(sheet);
    return sheet;
  }

  function applyFilters(state, now) {
    const cards = document.querySelectorAll("[data-filterable]");
    let visible = 0;
    cards.forEach((card) => {
      const hours = (() => {
        try { return JSON.parse(card.getAttribute("data-hours") || "null"); }
        catch { return null; }
      })();
      const distance = parseFloat(card.getAttribute("data-distance") || "0");

      let show = true;
      if (state.openNow && hasAnyHours(hours)) {
        show = show && isOpenAt(hours, now);
      } else if (state.openNow && !hasAnyHours(hours)) {
        /* By-appointment places fail the "open now" filter. */
        show = false;
      }
      if (state.maxDistance !== "any") {
        const limit = parseFloat(state.maxDistance);
        show = show && distance <= limit;
      }
      card.hidden = !show;
      if (show) visible += 1;
    });

    /* Update the count label and any "no matches" message. */
    const countEl = document.querySelector("[data-filter-count]");
    if (countEl) {
      const total = cards.length;
      countEl.textContent = visible === total
        ? `${total} places`
        : `${visible} of ${total} places`;
    }
    const noMatches = document.querySelector("[data-no-matches]");
    if (noMatches) noMatches.hidden = visible !== 0;

    /* Toggle the topbar filter button's "active" indicator. */
    const trigger = document.querySelector("[data-filter-open]");
    if (trigger && trigger.matches("button")) {
      const isActive = state.openNow || state.maxDistance !== "any";
      trigger.classList.toggle("is-active", isActive);
    }
  }

  function initFilters(now) {
    const trigger = document.querySelector("button[data-filter-open]");
    if (!trigger) return;
    /* If there's no filterable content on this page, skip. */
    if (!document.querySelector("[data-filterable]")) return;

    const sheet = buildFilterSheet();
    const state = { openNow: false, maxDistance: "any" };

    function open() {
      sheet.setAttribute("data-open", "true");
      document.documentElement.style.overflow = "hidden";
    }
    function close() {
      sheet.setAttribute("data-open", "false");
      document.documentElement.style.overflow = "";
    }

    trigger.addEventListener("click", open);
    sheet.addEventListener("click", (e) => {
      if (e.target.matches("[data-close]") || e.target.closest("[data-close]")) close();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && sheet.getAttribute("data-open") === "true") close();
    });

    const openInput = sheet.querySelector("[data-filter-open]");
    openInput.addEventListener("change", () => {
      state.openNow = openInput.checked;
      applyFilters(state, now);
    });

    sheet.querySelectorAll("[data-distance]").forEach((chip) => {
      chip.addEventListener("click", () => {
        state.maxDistance = chip.getAttribute("data-distance");
        sheet.querySelectorAll("[data-distance]").forEach((c) => {
          const on = c === chip;
          c.classList.toggle("is-active", on);
          c.setAttribute("aria-pressed", on ? "true" : "false");
        });
        applyFilters(state, now);
      });
    });

    const reset = sheet.querySelector("[data-filter-reset]");
    reset.addEventListener("click", () => {
      state.openNow = false;
      state.maxDistance = "any";
      openInput.checked = false;
      sheet.querySelectorAll("[data-distance]").forEach((c) => {
        const on = c.getAttribute("data-distance") === "any";
        c.classList.toggle("is-active", on);
        c.setAttribute("aria-pressed", on ? "true" : "false");
      });
      applyFilters(state, now);
    });

    /* Initial pass so the count label populates. */
    applyFilters(state, now);
  }

  /* ── Init ───────────────────────────────────────────────────────── */

  function init() {
    const now = sydneyNow();
    renderAllPills(now);
    renderHoursTable(now);
    initFilters(now);
    /* Refresh every minute so the pill state stays accurate without
       a manual reload. */
    setInterval(() => {
      const n = sydneyNow();
      renderAllPills(n);
      renderHoursTable(n);
    }, 60_000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
