/* Ask — Claude, the in-guide concierge.

   This is the conversational surface for the Beachcomber Guide. It
   ships with a slim venue table inlined into window.GUIDE.venues
   so the responder can render venue cards client-side without a
   fetch. The hotel's phone is inlined too so out-of-scope questions
   can hand off with a tap-to-call.

   The responder here is a templated, intent-routed stub. The real
   Claude API will plug in at `respond()` — everything around it
   (multi-turn rendering, venue cards, the front-desk handoff, the
   typing indicator) is the production UI. */

(function () {
  "use strict";

  /* ── Constants & inlined data ─────────────────────────────────── */

  const GUIDE = window.GUIDE || { hotel: {}, venues: [] };
  const VENUES = GUIDE.venues || [];
  const HOTEL = GUIDE.hotel || {};

  /* Per-venue traits drive intent routing. Derived by hand from the
     content because the JSON doesn't carry tags. Keeping it here (not
     in advertisers.json) means content edits don't have to think about
     the chat — and a real Claude backend will replace this anyway. */
  const TRAITS = {
    "beachie-bar-and-bistro":    ["dinner", "lunch", "breakfast", "casual", "view", "kids", "drinks", "coffee"],
    "pelicans-restaurant":       ["dinner", "lunch", "breakfast", "view", "quiet"],
    "mexicoast-cantina":         ["dinner", "casual", "drinks"],
    "dunes-by-dish":             ["dinner", "lunch", "view", "casual"],
    "the-savoy-bar-and-music":   ["dinner", "drinks", "music", "casual"],
    "cue-and-crew":              ["dinner", "lunch", "casual", "kids"],
    "wyong-milk-factory":        ["breakfast", "coffee", "lunch", "kids", "rainy", "quiet"],
    "distillery-botanica":       ["drinks", "rainy", "unique"],
    "chocolate-factory-gosford": ["coffee", "rainy", "kids", "unique"],
    "mangkorn-massage":          ["spa", "rainy", "quiet"],
    "wildfire-day-spa":          ["spa", "rainy", "quiet"],
    "ken-duncan-gallery":        ["rainy", "quiet", "unique"],
    "plain-janes-store":         ["rainy", "quiet", "shopping"],
    "coastal-hatters":           ["rainy", "unique", "shopping"],
    "bateau-tuggerah":           ["kids", "unique", "outdoors"],
    "central-coast-aero-club":   ["unique", "outdoors"],
    "amazement-farm-fun-park":   ["kids", "outdoors"],
    "iris-lodge-alpacas":        ["kids", "unique", "quiet"],
    "treetops-adventure":        ["kids", "outdoors"],
    "australian-reptile-park":   ["kids", "rainy"],
    "broken-bay-pearl-farm":     ["unique", "outdoors"],
  };

  const SPOKES_SVG =
    '<svg viewBox="0 0 24 24" aria-hidden="true">' +
    '<path d="M12 2v8M12 14v8M2 12h8M14 12h8M4.93 4.93l5.66 5.66M13.41 13.41l5.66 5.66M4.93 19.07l5.66-5.66M13.41 10.59l5.66-5.66" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/>' +
    '</svg>';

  /* ── DOM ──────────────────────────────────────────────────────── */

  const root = document.querySelector("[data-ask]");
  if (!root) return;

  const greetingEl = root.querySelector("[data-greeting]");
  const logEl = root.querySelector("[data-log]");
  const startersEl = root.querySelector("[data-starters]");
  const form = document.querySelector("[data-form]");
  const input = form && form.querySelector("[data-input]");
  const sendBtn = form && form.querySelector("[data-send]");

  /* ── Time-aware greeting ──────────────────────────────────────── */

  function buildGreeting() {
    const now = new Date();
    const hour = now.getHours();
    const day = now.getDay(); /* 0=Sun … 6=Sat */
    const weekdayName = ["Sunday", "Monday", "Tuesday", "Wednesday",
                         "Thursday", "Friday", "Saturday"][day];
    const isWeekend = day === 0 || day === 6;
    const isFriday = day === 5;

    let part;
    if (hour < 5)       part = "night";
    else if (hour < 11) part = "morning";
    else if (hour < 17) part = "afternoon";
    else if (hour < 21) part = "evening";
    else                part = "night";

    let tail;
    if (isFriday && part === "afternoon") {
      tail = "It's a " + weekdayName + " " + part + " at The Beachie. What's on?";
    } else if (isWeekend && part === "morning") {
      tail = weekdayName + " morning at The Beachie. What's the plan?";
    } else if (isWeekend && part === "evening") {
      tail = weekdayName + " evening at The Beachie. Settling in?";
    } else if (part === "night") {
      tail = "Late one tonight. What can I help with?";
    } else if (part === "morning") {
      tail = weekdayName + " morning at The Beachie. What's the plan?";
    } else {
      tail = weekdayName + " " + part + " at The Beachie. What can I help with?";
    }

    return "Hi, I'm Claude. " + tail;
  }

  if (greetingEl) greetingEl.textContent = buildGreeting();

  /* ── Venue helpers ────────────────────────────────────────────── */

  function findBySlug(slug) {
    for (let i = 0; i < VENUES.length; i++) {
      if (VENUES[i].slug === slug) return VENUES[i];
    }
    return null;
  }

  function pickVenuesByTraits(needed, opts) {
    /* `needed` is an array of trait strings; a venue matches if it
       has at least one trait from `needed`. opts can limit to a
       category group and cap the count. Results are sorted by drive
       time so the closest options surface first. */
    const o = opts || {};
    const limit = o.limit || 4;
    const group = o.group || null;
    const matches = [];
    for (let i = 0; i < VENUES.length; i++) {
      const v = VENUES[i];
      const traits = TRAITS[v.slug] || [];
      if (group && v.group !== group) continue;
      let ok = false;
      for (let j = 0; j < needed.length; j++) {
        if (traits.indexOf(needed[j]) !== -1) { ok = true; break; }
      }
      if (ok) matches.push(v);
    }
    matches.sort((a, b) => a.distance - b.distance);
    return matches.slice(0, limit);
  }

  /* ── Responder ────────────────────────────────────────────────────
     Templated intent matching. The shape of every reply is:

       { lede:    "Assistant message before the cards (or just text)",
         venues:  [slugs...],         // 0+ venue cards
         followup:"Optional tail message after the cards",
         handoff: { lede, button }    // Optional front-desk handoff }

     Intents are tried in order; the first match wins. */

  function respond(text) {
    const q = (text || "").toLowerCase();

    /* Front-desk / hotel-ops handoff: things the chat shouldn't answer
       because they're operationally specific to the property. */
    if (/(late check.?out|late check ?in|early check ?in|extend.*stay|extra night)/i.test(q)) {
      return {
        lede: "Late check-out is sometimes available, but it depends on the day's bookings — the front desk is the best (and only) source of truth.",
        handoff: { lede: "Tap to ring reception on", button: "Call reception" }
      };
    }
    if (/(front desk|reception|housekeep|maintenance|towel|wifi|password|room key|lost|complain|invoice|receipt|payment)/i.test(q)) {
      return {
        lede: "That one's reception — they handle anything operational on the property.",
        handoff: { lede: "Tap to ring the front desk on", button: "Call reception" }
      };
    }
    /* External services the guide doesn't carry. */
    if (/(pharmacy|chemist|doctor|hospital|surf report|weather|tide|petrol|servo|chemist|atm|bank)/i.test(q)) {
      return {
        lede: "That's outside what I know from the guide — the front desk handles those local logistics.",
        handoff: { lede: "Tap to call reception on", button: "Call reception" }
      };
    }

    /* Greetings — answer briefly and offer the chips' menu. */
    if (/^(hi|hello|hey|g'day|good (morning|afternoon|evening))[\s!.?]*$/i.test(q)) {
      return {
        lede: "Hello — happy to help. Tell me a meal, a time, or a mood and I'll point you somewhere good. Or pick one of the prompts above."
      };
    }

    /* Kids — Saturday-with-kids style itinerary. */
    if (/(kids|family|children|toddler|child)/i.test(q)) {
      const morning = pickVenuesByTraits(["kids"], { group: "things-to-do", limit: 2 });
      const lunch = pickVenuesByTraits(["kids", "casual"], { group: "eat-and-drink", limit: 1 });
      const afternoon = pickVenuesByTraits(["kids"], { group: "things-to-do", limit: 4 });
      /* Pick a different afternoon stop from the morning. */
      const morningSlugs = morning.map(v => v.slug);
      const altAfternoon = afternoon.filter(v => morningSlugs.indexOf(v.slug) === -1).slice(0, 1);
      const venues = morning.slice(0, 1).concat(lunch, altAfternoon).map(v => v.slug);
      return {
        lede: "Here's a day that works with kids — a morning out, a casual lunch, and an afternoon stop with plenty to do.",
        venues: venues,
        followup: "All under 30 minutes from the hotel. Want a rainy-day variant?"
      };
    }

    /* Rainy / weather-affected. */
    if (/(rain|wet|indoor|inside|bad weather)/i.test(q)) {
      const venues = pickVenuesByTraits(["rainy"], { limit: 4 }).map(v => v.slug);
      return {
        lede: "Plenty of indoor or roof-covered options on the Coast. These are my picks if the weather closes in:",
        venues: venues
      };
    }

    /* Coffee — quiet morning leaning. */
    if (/(coffee|breakfast|brunch|morning)/i.test(q)) {
      const venues = pickVenuesByTraits(["coffee", "breakfast"], { limit: 3 }).map(v => v.slug);
      return {
        lede: "For a quiet morning coffee — closest first:",
        venues: venues
      };
    }

    /* Spa / massage / unwind. */
    if (/(spa|massage|relax|unwind|treatment|sore)/i.test(q)) {
      const venues = pickVenuesByTraits(["spa"], { limit: 2 }).map(v => v.slug);
      return {
        lede: "Two places I'd send you — both within a few minutes of the hotel:",
        venues: venues
      };
    }

    /* Drinks / bar / sunset. */
    if (/(drink|wine|cocktail|bar|sunset|after work)/i.test(q)) {
      const venues = pickVenuesByTraits(["drinks", "view"], { limit: 3 }).map(v => v.slug);
      return {
        lede: "For an evening drink — view-first picks at the top:",
        venues: venues
      };
    }

    /* "Unique" / surprise me. */
    if (/(surprise|unique|unusual|different|special|one of a kind)/i.test(q)) {
      const venues = pickVenuesByTraits(["unique"], { limit: 3 }).map(v => v.slug);
      return {
        lede: "Three that feel like nowhere else on the Coast:",
        venues: venues,
        followup: "Tell me if you want longer drives ruled out."
      };
    }

    /* Casual dinner / dinner / eat tonight. */
    if (/(casual|easy|relax).*(dinner|eat)|dinner.*(tonight|casual|easy)|(eat|dinner|food)\b/i.test(q)) {
      const venues = pickVenuesByTraits(["dinner", "casual"], { group: "eat-and-drink", limit: 4 }).map(v => v.slug);
      return {
        lede: "Casual dinners, sorted closest to the hotel first:",
        venues: venues
      };
    }

    /* Lunch. */
    if (/(lunch|midday)/i.test(q)) {
      const venues = pickVenuesByTraits(["lunch"], { group: "eat-and-drink", limit: 4 }).map(v => v.slug);
      return {
        lede: "Lunch spots — closest first:",
        venues: venues
      };
    }

    /* Generic "what's on / what to do / things to do today". */
    if (/(what'?s on|what to do|things to do|today|do today)/i.test(q)) {
      const venues = pickVenuesByTraits(["kids", "unique", "outdoors"], { group: "things-to-do", limit: 4 }).map(v => v.slug);
      return {
        lede: "A few options nearby — anything jump out?",
        venues: venues
      };
    }

    /* Default — gentle nudge to a starter. */
    return {
      lede: "I can help with eating, drinking, things to do, and how a day might string together. Tell me a meal, a time of day, or a mood — or pick one of the prompts above."
    };
  }

  /* ── Rendering ────────────────────────────────────────────────── */

  function el(tag, cls, html) {
    const e = document.createElement(tag);
    if (cls) e.className = cls;
    if (html != null) e.innerHTML = html;
    return e;
  }

  function escapeHtml(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function distanceLabel(v) {
    if (v.distance === 0) return v.suburb + " · At the hotel";
    return v.suburb + " · " + v.distance + " min from the hotel";
  }

  function directionsHref(v) {
    const q = (v.name + " " + (v.address || "")).trim();
    return "https://maps.google.com/?q=" + encodeURIComponent(q);
  }

  function renderVenueCard(slug) {
    const v = findBySlug(slug);
    if (!v) return null;
    const card = el("a", "venue-card");
    card.href = "/" + v.slug + "/";

    const media = el("div", "venue-card__media");
    const img = document.createElement("img");
    img.src = v.image; img.alt = ""; img.loading = "lazy"; img.decoding = "async";
    media.appendChild(img);

    const body = el("div", "venue-card__body");
    body.appendChild(el("span", "venue-card__cat", escapeHtml(v.category)));
    body.appendChild(el("h3", "venue-card__name", escapeHtml(v.name)));
    body.appendChild(el("p", "venue-card__meta", escapeHtml(distanceLabel(v))));
    if (v.perk) body.appendChild(el("p", "venue-card__perk", escapeHtml(v.perk)));

    const actions = el("div", "venue-card__actions");
    actions.appendChild(linkAction("View page", "/" + v.slug + "/", "primary"));
    if (v.booking_url) actions.appendChild(linkAction("Book", v.booking_url));
    actions.appendChild(linkAction("Directions", directionsHref(v)));

    card.appendChild(media);
    card.appendChild(body);
    card.appendChild(actions);
    return card;
  }

  function linkAction(label, href, variant) {
    const a = document.createElement("a");
    a.className = "venue-card__action" + (variant === "primary" ? " venue-card__action--primary" : "");
    a.href = href;
    a.textContent = label;
    /* Don't trigger the card's wrapping link. */
    a.addEventListener("click", (e) => e.stopPropagation());
    return a;
  }

  function pushUser(text) {
    const m = el("div", "msg msg--user");
    m.textContent = text;
    logEl.appendChild(m);
  }

  function buildMark() {
    const w = el("span", "msg__mark");
    w.innerHTML = SPOKES_SVG;
    return w;
  }

  function pushAssistantText(text) {
    const m = el("div", "msg msg--concierge");
    m.appendChild(buildMark());
    m.appendChild(el("div", "msg__body", "<p>" + escapeHtml(text) + "</p>"));
    logEl.appendChild(m);
  }

  function pushAssistantCards(slugs) {
    const m = el("div", "msg msg--concierge");
    m.appendChild(buildMark());
    const body = el("div", "msg__body");
    slugs.forEach(slug => {
      const card = renderVenueCard(slug);
      if (card) body.appendChild(card);
    });
    if (!body.children.length) return; /* don't render empty wrappers */
    m.appendChild(body);
    logEl.appendChild(m);
  }

  function pushHandoff(payload) {
    const m = el("div", "msg msg--concierge");
    m.appendChild(buildMark());
    const body = el("div", "msg__body");
    const card = el("div", "handoff");
    /* The lede carries the phone number so the button can stay compact
       and one-line-only on every viewport. */
    const ledeText = HOTEL.phone
      ? payload.lede + " " + HOTEL.phone + "."
      : payload.lede;
    card.appendChild(el("p", "handoff__lede", escapeHtml(ledeText)));
    if (HOTEL.phone_href) {
      const a = document.createElement("a");
      a.className = "handoff__call";
      a.href = HOTEL.phone_href;
      a.innerHTML =
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' +
        '<path d="M5 4h3l2 5-2.5 1.5a12 12 0 0 0 6 6L15 14l5 2v3a2 2 0 0 1-2 2A15 15 0 0 1 3 6a2 2 0 0 1 2-2z"/></svg>' +
        '<span>' + escapeHtml(payload.button) + '</span>';
      card.appendChild(a);
    }
    body.appendChild(card);
    m.appendChild(body);
    logEl.appendChild(m);
  }

  function pushTyping() {
    const m = el("div", "msg msg--concierge msg--typing");
    m.appendChild(buildMark());
    m.appendChild(el("div", "msg__body", "<span></span><span></span><span></span>"));
    logEl.appendChild(m);
    return m;
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    });
  }

  /* ── Conversation flow ────────────────────────────────────────── */

  function setConversing() {
    root.setAttribute("data-state", "conversing");
  }

  function handleUserMessage(text) {
    setConversing();
    pushUser(text);
    scrollToBottom();

    /* Brief, life-like delay so the typing indicator registers. */
    const typing = pushTyping();
    scrollToBottom();
    setTimeout(() => {
      typing.remove();
      const r = respond(text);
      if (r.lede) pushAssistantText(r.lede);
      if (r.venues && r.venues.length) pushAssistantCards(r.venues);
      if (r.followup) pushAssistantText(r.followup);
      if (r.handoff) pushHandoff(r.handoff);
      scrollToBottom();
    }, 540 + Math.random() * 360);
  }

  /* ── Compose bar ──────────────────────────────────────────────── */

  function syncSendState() {
    if (!sendBtn || !input) return;
    sendBtn.disabled = input.value.trim().length === 0;
  }
  if (input) input.addEventListener("input", syncSendState);
  syncSendState();

  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const v = (input.value || "").trim();
      if (!v) return;
      input.value = "";
      syncSendState();
      handleUserMessage(v);
    });
  }

  /* ── Starter chips ────────────────────────────────────────────── */

  if (startersEl) {
    startersEl.addEventListener("click", (e) => {
      const chip = e.target.closest("[data-starter]");
      if (!chip) return;
      const v = (chip.textContent || "").trim();
      if (!v) return;
      handleUserMessage(v);
    });
  }
})();
