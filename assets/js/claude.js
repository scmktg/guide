/* Claude — context-aware floating prompt bar.

   How it works:
   1. We render a single .claude-bar fixed at the bottom of the viewport.
   2. We watch every element on the page with [data-claude-section] using
      an IntersectionObserver. As the user scrolls, we figure out which
      section is most prominently in view and read its data-* attributes:
        - data-claude-topic   (key into TOPICS for the chat sheet intro)
        - data-claude-prompt  (the bar's display text)
        - data-claude-name    (optional, substituted into {name})
      The bar's prompt label fades and swaps to the new text.
   3. Tapping the bar opens the chat sheet pre-loaded with that topic.

   Live Claude wiring is the obvious follow-up — swap findReply() and
   you're done. */

(function () {
  "use strict";

  const TOPICS = {
    "guide": {
      label: "About the guide",
      intro:
        "Hi — I'm Claude. The Beachcomber Guide is a curated companion for your stay: the hotel itself, the places we'd send a friend to eat or drink, the things worth doing on the Central Coast, and a map to tie it all together. Tell me what you're in the mood for and I'll point you in a direction.",
      suggestions: [
        "What's good for sunset?",
        "I'm here just one night",
        "Best lunch within 15 minutes?"
      ]
    },
    "hotel": {
      label: "About the hotel",
      intro:
        "The Beachcomber Hotel & Resort is a Hamptons-inspired waterfront retreat on Tuggerah Lake in Toukley. Pelicans and the Beachie are on-site; the lake is at the back door. Ask me anything about facilities, check-in or what's nearby.",
      suggestions: [
        "What time is check-in?",
        "Is there parking?",
        "What's on-site dining like?"
      ]
    },
    "facilities": {
      label: "Hotel facilities",
      intro:
        "Pool, on-site dining, waterfront access on Tuggerah Lake, and a short stroll into Toukley. What do you want to check on?",
      suggestions: [
        "Is there a gym?",
        "Pet friendly?",
        "Family rooms?"
      ]
    },
    "dining": {
      label: "Eat at the hotel",
      intro:
        "Two ways to settle in without leaving the property: Pelicans is the restaurant — broader menu, slower meals; the Beachie Bar & Bistro is more casual. Both face the lake.",
      suggestions: [
        "Best for breakfast?",
        "Kid-friendly menu?",
        "Do I need to book?"
      ]
    },
    "eat-listings": {
      label: "Where to eat & drink",
      intro:
        "Every restaurant, bar and food maker in the guide, sorted by drive time from the hotel. From a five-minute bistro to a half-day at a distillery. What sort of meal are you after?",
      suggestions: [
        "A long lunch",
        "Coffee + something sweet",
        "Drinks with a view"
      ]
    },
    "do-listings": {
      label: "Things to do",
      intro:
        "Experiences, tours and standout local stops — every one within easy reach of the hotel. Tell me the time you have and the company you're with and I'll narrow it down.",
      suggestions: [
        "Two hours, just us",
        "Half-day with kids",
        "Rainy-day options?"
      ]
    },
    "map": {
      label: "The local map",
      intro:
        "Every recommendation pinned on one map of the Central Coast. The hotel is the dark pin; eat & drink are warm, things to do are cool. Tap any pin for the basics and a link to its page.",
      suggestions: [
        "What's closest to the hotel?",
        "A loop for the day?",
        "Best beach drive?"
      ]
    },
    "place": {
      label: "About {name}",
      intro:
        "{name} is one of our picks in this guide. Ask me anything about what to expect, who it suits, how long to allow, or how it fits into a day on the Coast.",
      suggestions: [
        "Tell me about {name}",
        "Who's it best for?",
        "How long should I allow?"
      ]
    },
    "perk": {
      label: "Guest perk",
      intro:
        "The guest perk is yours as a Beachcomber guest — show this page or quote the code when you arrive. Ask me how to redeem it or what's included.",
      suggestions: [
        "How do I redeem this?",
        "Any conditions?",
        "Can I share it?"
      ]
    },
    "visit": {
      label: "Visit & connect",
      intro:
        "Best ways to get in touch or get there. Want directions, hours, or to know whether to book ahead?",
      suggestions: [
        "How far from the hotel?",
        "Do I need to book?",
        "Best time to arrive?"
      ]
    },
    "gallery": {
      label: "From the visit",
      intro:
        "These are images from {name}. Anything in particular you'd like to know more about?",
      suggestions: [
        "What's the photography brief?",
        "Best photo spots here?",
        "Is photography welcome?"
      ]
    }
  };

  /* Keyword → reply lookup (matches first hit). */
  const TEMPLATED_REPLIES = [
    ["check-in", "Standard check-in is from 3pm and check-out is by 10am. Early arrivals can drop bags at reception; late check-out is sometimes possible — just ask the front desk."],
    ["check in", "Standard check-in is from 3pm and check-out is by 10am. Early arrivals can drop bags at reception; late check-out is sometimes possible — just ask the front desk."],
    ["check out", "Standard check-out is by 10am. Late check-out is sometimes available depending on the day's bookings — worth a quick ask at reception the night before."],
    ["parking", "Yes — free on-site parking for guests, right at the hotel."],
    ["gym", "There's no dedicated gym, but the lake walking track is right at the doorstep and there are local gyms within a few minutes' drive — ask reception for a day pass recommendation."],
    ["pet", "The hotel isn't pet-friendly inside the rooms, but several of the dining venues in the guide welcome well-behaved dogs in their outdoor areas."],
    ["family", "Yes — family rooms are available. Both on-site dining venues have kid-friendly menus, and the lake park next door has plenty of space to burn off energy."],
    ["breakfast", "Pelicans does a proper sit-down breakfast that opens early. The Beachie does a slightly later, lighter breakfast with the same lake view."],
    ["book", "Bookings aren't strictly required, but on weekends and over school holidays they're a good idea — especially for lunch venues. Most pages list a phone number."],
    ["sunset", "For sunset: the Beachie deck at the hotel itself is hard to beat. If you want to drive, Soldiers Beach lookout (15 minutes) puts the Pacific in front of you instead of the lake."],
    ["one night", "If you've got just one night: drinks and dinner at the Beachie, a slow morning at Pelicans, then a single big stop on the way out — Distillery Botanica or Ken Duncan Gallery are both worth the detour."],
    ["lunch", "Within 15 minutes of the hotel: Pelicans (in-house), Dunes by Dish (beachside), or the Wyong Milk Factory for a sunny courtyard. Cue and Crew is a longer-but-rewarding drive for serious BBQ."],
    ["rain", "Rainy-day picks: Ken Duncan Gallery, Chocolate Factory Gosford, Distillery Botanica, Mangkorn Massage. The Reptile Park is partly indoors too if you've got kids in tow."],
    ["kids", "With kids: Australian Reptile Park, Amazement Farm & Fun Park, Iris Lodge Alpacas, Treetops Adventure. The map page is the fastest way to pick by drive time."],
    ["closest", "Closest to the hotel are the on-site venues (Pelicans, Beachie) and Mangkorn Massage. The Wyong Milk Factory and Dunes by Dish are both under ten minutes."],
    ["how far", "Every page lists its drive time from the hotel near the top. Most stops in the guide are under 30 minutes; the furthest are about an hour."],
    ["redeem", "Show this page to the staff when you arrive, or quote the code on it at the time of booking. Most perks are honoured for the duration of your stay — no expiry games."],
    ["share", "Perks are intended per booked room — staff are friendly about it, but if you're travelling with friends in a separate room they should bring their own copy of the guide."],
    ["coffee", "For coffee with something sweet, the Chocolate Factory Gosford and Wyong Milk Factory both nail it. Closer to the hotel, the Beachie does a solid flat white."],
    ["view", "For drinks with a view: the Beachie deck at the hotel, Pelicans windows at sunset, or a longer drive to The Savoy Bar & Music for a different kind of room."]
  ];

  function findReply(topic, text, ctx) {
    const lower = (text || "").toLowerCase().trim();
    for (let i = 0; i < TEMPLATED_REPLIES.length; i++) {
      if (lower.indexOf(TEMPLATED_REPLIES[i][0]) !== -1) {
        return TEMPLATED_REPLIES[i][1];
      }
    }
    const t = TOPICS[topic];
    const name = (ctx && ctx.name) || "this listing";
    const label = t ? substitute(t.label, ctx).toLowerCase() : "this section";
    return (
      "Good question. *I'm answering from a small set of templates while a live connection to Claude is wired in.* In the meantime, the page itself has the essentials, and the front desk at the Beachcomber is always happy to help — especially with questions about " + label + "."
    );
  }

  function substitute(s, ctx) {
    if (!s) return s;
    const name = (ctx && ctx.name) || "this place";
    return s.replace(/\{name\}/g, name);
  }

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function makeMark() {
    const span = document.createElement("span");
    span.className = "claude-mark";
    span.innerHTML =
      '<svg viewBox="0 0 24 24" aria-hidden="true">' +
      '<path d="M12 2v8M12 14v8M2 12h8M14 12h8M4.93 4.93l5.66 5.66M13.41 13.41l5.66 5.66M4.93 19.07l5.66-5.66M13.41 10.59l5.66-5.66" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/>' +
      "</svg>";
    return span;
  }

  /* ── The bar ─────────────────────────────────────────────────────── */

  function buildBar() {
    const bar = document.createElement("button");
    bar.type = "button";
    bar.className = "claude-bar";
    bar.setAttribute("aria-label", "Ask Claude");
    bar.innerHTML =
      '<span class="claude-bar__mark-slot"></span>' +
      '<span class="claude-bar__prompt" data-bar-prompt>Ask Claude about the guide</span>' +
      '<span class="claude-bar__arrow" aria-hidden="true">' +
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"><path d="M9 6l6 6-6 6"/></svg>' +
      '</span>';
    /* Inject the asterisk mark */
    const slot = bar.querySelector(".claude-bar__mark-slot");
    const mark = makeMark();
    mark.classList.add("claude-bar__mark");
    slot.replaceWith(mark);
    document.body.appendChild(bar);
    return bar;
  }

  let currentTopic = "guide";
  let currentName = "";

  function setBar(bar, topic, prompt, name) {
    const promptEl = bar.querySelector("[data-bar-prompt]");
    const next = substitute(prompt || "Ask Claude", { name: name });
    if (promptEl.textContent === next) return;
    currentTopic = topic || "guide";
    currentName = name || "";
    promptEl.classList.add("is-changing");
    setTimeout(() => {
      promptEl.textContent = next;
      promptEl.classList.remove("is-changing");
    }, 180);
  }

  function observeSections(bar) {
    const sections = Array.from(document.querySelectorAll("[data-claude-section]"));
    if (!sections.length) {
      bar.classList.add("is-ready");
      return;
    }

    /* Map of element → ratio. We pick whichever section has the largest
       intersection ratio at any given moment. */
    const ratios = new WeakMap();

    const update = () => {
      let best = null;
      let bestRatio = 0;
      sections.forEach((el) => {
        const r = ratios.get(el) || 0;
        if (r > bestRatio) {
          bestRatio = r;
          best = el;
        }
      });
      /* Fallback: if nothing is in view yet, use the first section. */
      const target = best || sections[0];
      const topic = target.getAttribute("data-claude-topic") || "guide";
      const prompt = target.getAttribute("data-claude-prompt") || "Ask Claude about this section";
      const name = target.getAttribute("data-claude-name") || "";
      setBar(bar, topic, prompt, name);
    };

    /* Multiple thresholds give smoother handoff between sections. */
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          ratios.set(entry.target, entry.intersectionRatio);
        });
        update();
      },
      {
        threshold: [0, 0.15, 0.3, 0.45, 0.6, 0.8, 1],
        /* Bias the viewport upward so the section behind the bottom-anchored
           bar still counts as "in view" until the next one really takes over. */
        rootMargin: "-10% 0px -25% 0px"
      }
    );
    sections.forEach((el) => observer.observe(el));

    /* Set an initial label, then reveal the bar after a beat. */
    update();
    requestAnimationFrame(() => {
      requestAnimationFrame(() => bar.classList.add("is-ready"));
    });
  }

  /* ── The sheet ───────────────────────────────────────────────────── */

  function buildSheet() {
    const sheet = document.createElement("div");
    sheet.className = "claude-sheet";
    sheet.setAttribute("role", "dialog");
    sheet.setAttribute("aria-modal", "true");
    sheet.setAttribute("aria-labelledby", "claude-sheet-title");
    sheet.innerHTML =
      '<div class="claude-sheet__scrim" data-close></div>' +
      '<div class="claude-sheet__panel">' +
        '<div class="claude-sheet__grabber" aria-hidden="true"></div>' +
        '<div class="claude-sheet__header">' +
          '<div class="claude-sheet__title" id="claude-sheet-title">' +
            '<span class="claude-sheet__mark-slot"></span>' +
            '<span>Claude</span>' +
          '</div>' +
          '<span class="claude-sheet__sub" data-topic-label></span>' +
          '<button class="claude-sheet__close" data-close aria-label="Close">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">' +
              '<path d="M6 6l12 12M18 6L6 18"/>' +
            '</svg>' +
          '</button>' +
        '</div>' +
        '<div class="claude-sheet__log" data-log></div>' +
        '<div class="claude-sheet__suggestions" data-suggestions></div>' +
        '<form class="claude-sheet__form" data-form>' +
          '<input class="claude-sheet__input" type="text" placeholder="Ask Claude about this…" data-input autocomplete="off" />' +
          '<button class="claude-sheet__send" type="submit" aria-label="Send">' +
            '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
              '<path d="M4 12l16-8-6 18-3-7-7-3z"/>' +
            '</svg>' +
          '</button>' +
        '</form>' +
        '<div class="claude-sheet__foot">Templated responses · Live Claude coming soon</div>' +
      '</div>';
    const headerMark = makeMark();
    sheet.querySelector(".claude-sheet__mark-slot").replaceWith(headerMark);
    document.body.appendChild(sheet);
    return sheet;
  }

  function pushUser(log, text) {
    const el = document.createElement("div");
    el.className = "claude-msg claude-msg--user";
    el.textContent = text;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  function pushAssistant(log, text) {
    const el = document.createElement("div");
    el.className = "claude-msg claude-msg--assistant";
    const mark = makeMark();
    const body = document.createElement("div");
    body.className = "claude-msg__body";
    body.innerHTML = escapeHtml(text).replace(/\*(.+?)\*/g, "<em>$1</em>");
    el.appendChild(mark);
    el.appendChild(body);
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
  }

  function pushTyping(log) {
    const el = document.createElement("div");
    el.className = "claude-msg claude-msg--assistant claude-msg--typing";
    const mark = makeMark();
    const body = document.createElement("div");
    body.className = "claude-msg__body";
    body.innerHTML = "<span></span><span></span><span></span>";
    el.appendChild(mark);
    el.appendChild(body);
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
    return el;
  }

  function openSheet(sheet, bar) {
    const topicKey = currentTopic;
    const ctx = { name: currentName };
    const topic = TOPICS[topicKey] || TOPICS["guide"];
    const log = sheet.querySelector("[data-log]");
    const suggestions = sheet.querySelector("[data-suggestions]");
    const sub = sheet.querySelector("[data-topic-label]");
    const input = sheet.querySelector("[data-input]");

    log.innerHTML = "";
    suggestions.innerHTML = "";
    const label = substitute(topic.label, ctx);
    sub.textContent = label;

    pushAssistant(log, substitute(topic.intro, ctx));
    topic.suggestions.forEach((s) => {
      const text = substitute(s, ctx);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "claude-suggestion";
      btn.textContent = text;
      btn.addEventListener("click", () => handleSubmit(sheet, text, ctx));
      suggestions.appendChild(btn);
    });

    sheet.setAttribute("data-open", "true");
    sheet.dataset.currentTopic = topicKey;
    sheet.dataset.currentName = currentName;
    if (bar) bar.classList.add("is-hidden");
    document.documentElement.style.overflow = "hidden";
    setTimeout(() => input.focus({ preventScroll: true }), 320);
  }

  function closeSheet(sheet, bar) {
    sheet.setAttribute("data-open", "false");
    if (bar) bar.classList.remove("is-hidden");
    document.documentElement.style.overflow = "";
  }

  function handleSubmit(sheet, text, ctxArg) {
    const log = sheet.querySelector("[data-log]");
    const topicKey = sheet.dataset.currentTopic;
    const ctx = ctxArg || { name: sheet.dataset.currentName || "" };
    pushUser(log, text);
    const typing = pushTyping(log);
    setTimeout(() => {
      typing.remove();
      pushAssistant(log, findReply(topicKey, text, ctx));
    }, 520 + Math.random() * 380);
  }

  function init() {
    const bar = buildBar();
    const sheet = buildSheet();
    const form = sheet.querySelector("[data-form]");
    const input = sheet.querySelector("[data-input]");

    bar.addEventListener("click", () => openSheet(sheet, bar));

    sheet.addEventListener("click", (e) => {
      if (e.target.matches("[data-close]") || e.target.closest("[data-close]")) {
        closeSheet(sheet, bar);
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && sheet.getAttribute("data-open") === "true") {
        closeSheet(sheet, bar);
      }
    });

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const v = input.value.trim();
      if (!v) return;
      input.value = "";
      handleSubmit(sheet, v);
    });

    observeSections(bar);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
