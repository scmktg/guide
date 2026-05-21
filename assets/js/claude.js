/* Claude chat sheet — templated responses (live API coming later).
   Wire-up: any element with [data-claude-topic="…"] opens the sheet
   pre-loaded with that topic's intro + suggested prompts. An optional
   [data-claude-name="<business>"] substitutes into {name} placeholders. */

(function () {
  "use strict";

  /* ── Topic library ─────────────────────────────────────────────── */
  /* {name} = the business / page subject, supplied via data-claude-name */

  const TOPICS = {
    /* Home / guide-level */
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
        "The Beachcomber Hotel & Resort is a Hamptons-inspired waterfront retreat on Tuggerah Lake in Toukley. It has two on-site venues (Pelicans Restaurant and Beachie Bar & Bistro), a pool, and direct lake access. Ask me anything about facilities, check-in or what's nearby.",
      suggestions: [
        "What time is check-in?",
        "Is there parking?",
        "What's on-site dining like?"
      ]
    },
    "facilities": {
      label: "Hotel facilities",
      intro:
        "Pool, on-site dining at Pelicans and the Beachie, waterfront access on Tuggerah Lake, and a short stroll into Toukley. Anything specific you want to check?",
      suggestions: [
        "Is there a gym?",
        "Pet friendly?",
        "Family rooms?"
      ]
    },
    "dining": {
      label: "Eat at the hotel",
      intro:
        "Two ways to settle in without leaving the property: Pelicans is the restaurant — broader menu, slower meals; Beachie Bar & Bistro is more casual, good for a drink or a pub-style plate. Both look out over the lake.",
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
        "Every recommendation pinned on one map of the Central Coast. The hotel is the dark pin; eat & drink are warm, things to do are cool. Tap a pin to see the basics and jump to its page.",
      suggestions: [
        "What's closest to the hotel?",
        "A loop for the day?",
        "Best beach drive?"
      ]
    },

    /* Business-page topics — {name} substituted at open() time */
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
        "The guest perk is yours as a Beachcomber guest — show this page (or the code shown on it) when you arrive. Ask me how to redeem it or what's included.",
      suggestions: [
        "How do I redeem this?",
        "Any conditions?",
        "Can I share it?"
      ]
    },
    "visit": {
      label: "Visit & connect",
      intro:
        "Best ways to get in touch or get there. Want directions, opening hours, or to know whether to book ahead?",
      suggestions: [
        "How far from the hotel?",
        "Do I need to book?",
        "Best time to arrive?"
      ]
    }
  };

  /* ── Keyword → reply lookup ───────────────────────────────────── */
  const TEMPLATED_REPLIES = [
    ["check-in", "Standard check-in is from 3pm and check-out is by 10am. Early arrivals can drop bags at reception; late check-out is sometimes possible — just ask the front desk."],
    ["check in", "Standard check-in is from 3pm and check-out is by 10am. Early arrivals can drop bags at reception; late check-out is sometimes possible — just ask the front desk."],
    ["check out", "Standard check-out is by 10am. Late check-out is sometimes available depending on the day's bookings — worth a quick ask at reception the night before."],
    ["parking", "Yes — free on-site parking for guests, right at the hotel."],
    ["gym", "There's no dedicated gym, but the lake walking track is right at the doorstep and there are local gyms within a few minutes' drive — ask reception for a day pass recommendation."],
    ["pet", "The hotel isn't pet-friendly inside the rooms, but several of the dining venues in the guide are welcoming to well-behaved dogs in their outdoor areas."],
    ["family", "Yes — family rooms are available. Both on-site dining venues have kid-friendly menus, and the lake park next door has plenty of space to burn off energy."],
    ["breakfast", "Pelicans does a proper sit-down breakfast that opens early. The Beachie does a slightly later, lighter breakfast with the same lake view."],
    ["book", "Bookings aren't strictly required, but on weekends and over school holidays it's a good idea — especially for the lunch venues. Most places in the guide list a phone number on their page."],
    ["sunset", "For sunset: the Beachie deck at the hotel itself is hard to beat. If you want to drive, Soldiers Beach lookout (15 minutes) puts the Pacific in front of you instead of the lake."],
    ["one night", "If you've got just one night: drinks and dinner at the Beachie, a slow morning at Pelicans, then a single big stop on the way out — Distillery Botanica or Ken Duncan Gallery are both worth the detour."],
    ["lunch", "Within 15 minutes of the hotel: Pelicans (in-house), Dunes by Dish (beachside), or the Wyong Milk Factory if you want a sunny courtyard. Cue and Crew is a longer-but-rewarding drive for serious BBQ."],
    ["rain", "Rainy-day picks: Ken Duncan Gallery, Chocolate Factory Gosford, Distillery Botanica, Mangkorn Massage. The Reptile Park is partly indoors too if you've got kids in tow."],
    ["kids", "With kids: Australian Reptile Park, Amazement Farm & Fun Park, Iris Lodge Alpacas, Treetops Adventure. The map page is the fastest way to pick by drive time."],
    ["closest", "Closest to the hotel are the on-site venues (Pelicans, Beachie) and Mangkorn Massage. The Wyong Milk Factory and Dunes by Dish are both under ten minutes."],
    ["how far", "Every page lists its drive time from the hotel near the top. Most stops in the guide are under 30 minutes; the furthest (Broken Bay Pearl Farm, Distillery Botanica) are about an hour."],
    ["redeem", "Show this page to the staff when you arrive, or quote the code on it at the time of booking. Most perks are honoured for the duration of your stay — no expiry date games."],
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
    const label = t ? (t.label || "this part of the guide") : "this part of the guide";
    const name = (ctx && ctx.name) || "this listing";
    return (
      "That's a good question. *I'm answering from a small set of templates while a live connection to Claude is wired in.* In the meantime: " +
      "the page itself has the essentials, and the front desk at the Beachcomber is always happy to help in person — especially if you're asking about " +
      label.toLowerCase().replace(/\{name\}/g, name) + "."
    );
  }

  function substitute(s, ctx) {
    if (!s) return s;
    const name = (ctx && ctx.name) || "this place";
    return s.replace(/\{name\}/g, name);
  }

  function makeMark() {
    const span = document.createElement("span");
    span.className = "claude-mark";
    span.innerHTML =
      '<svg viewBox="0 0 24 24" aria-hidden="true">' +
      '<path d="M12 2v8M12 14v8M2 12h8M14 12h8M4.93 4.93l5.66 5.66M13.41 13.41l5.66 5.66M4.93 19.07l5.66-5.66M13.41 10.59l5.66-5.66" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" fill="none"/>' +
      "</svg>";
    return span;
  }

  function escapeHtml(s) {
    return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

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
        '<div class="claude-sheet__topic" data-topic-pill></div>' +
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
    sheet.querySelector(".claude-sheet__mark-slot").replaceWith(makeMark());
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

  function openSheet(sheet, topicKey, ctx) {
    const topic = TOPICS[topicKey] || TOPICS["guide"];
    const log = sheet.querySelector("[data-log]");
    const suggestions = sheet.querySelector("[data-suggestions]");
    const pill = sheet.querySelector("[data-topic-pill]");
    const sub = sheet.querySelector("[data-topic-label]");
    const input = sheet.querySelector("[data-input]");

    log.innerHTML = "";
    suggestions.innerHTML = "";
    const label = substitute(topic.label, ctx);
    pill.textContent = label;
    sub.textContent = "Asking about · " + label;
    sheet.dataset.currentTopic = topicKey;
    sheet.dataset.currentName = (ctx && ctx.name) || "";

    pushAssistant(log, substitute(topic.intro, ctx));
    topic.suggestions.forEach((s) => {
      const text = substitute(s, ctx);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "claude-suggestion";
      btn.textContent = text;
      btn.addEventListener("click", () => handleSubmit(sheet, text));
      suggestions.appendChild(btn);
    });

    sheet.setAttribute("data-open", "true");
    document.documentElement.style.overflow = "hidden";
    setTimeout(() => input.focus({ preventScroll: true }), 320);
  }

  function closeSheet(sheet) {
    sheet.setAttribute("data-open", "false");
    document.documentElement.style.overflow = "";
  }

  function handleSubmit(sheet, text) {
    const log = sheet.querySelector("[data-log]");
    const topicKey = sheet.dataset.currentTopic;
    const ctx = { name: sheet.dataset.currentName || "" };
    pushUser(log, text);
    const typing = pushTyping(log);
    setTimeout(() => {
      typing.remove();
      pushAssistant(log, findReply(topicKey, text, ctx));
    }, 520 + Math.random() * 380);
  }

  function init() {
    const sheet = buildSheet();
    const form = sheet.querySelector("[data-form]");
    const input = sheet.querySelector("[data-input]");

    sheet.addEventListener("click", (e) => {
      if (e.target.matches("[data-close]") || e.target.closest("[data-close]")) {
        closeSheet(sheet);
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && sheet.getAttribute("data-open") === "true") {
        closeSheet(sheet);
      }
    });

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const v = input.value.trim();
      if (!v) return;
      input.value = "";
      handleSubmit(sheet, v);
    });

    document.querySelectorAll("[data-claude-topic]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        openSheet(sheet, btn.getAttribute("data-claude-topic"), {
          name: btn.getAttribute("data-claude-name") || ""
        });
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
