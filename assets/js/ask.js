/* Ask — the concierge.

   Single-page chat surface. The page ships with a slim venue table
   inlined into window.GUIDE.venues so the responder can render venue
   cards without a fetch. The hotel's phone is inlined too so the
   out-of-scope hand-off can offer a tap-to-call.

   This first pass covers the empty state: the time-aware greeting,
   the starter chips, and the compose bar. The full conversation flow
   (replies, venue cards, handoff) wires in next. */

(function () {
  "use strict";

  const root = document.querySelector("[data-ask]");
  if (!root) return;

  const greetingEl = root.querySelector("[data-greeting]");
  const startersEl = root.querySelector("[data-starters]");
  const logEl = root.querySelector("[data-log]");
  const form = document.querySelector("[data-form]");
  const input = form && form.querySelector("[data-input]");
  const sendBtn = form && form.querySelector("[data-send]");

  /* ── Time-aware greeting ──────────────────────────────────────────
     Built from the guest's local time/date. We don't have a weather
     feed wired in, so we keep the descriptor neutral ("It's a
     {weekday} {part-of-day}") — easy to layer real weather on later. */

  function buildGreeting() {
    const now = new Date();
    const hour = now.getHours();
    const day = now.getDay(); /* 0=Sun … 6=Sat */
    const weekdayName = ["Sunday", "Monday", "Tuesday", "Wednesday",
                         "Thursday", "Friday", "Saturday"][day];
    const isWeekend = day === 0 || day === 6;
    const isFriday = day === 5;

    let salute, part;
    if (hour < 5)       { salute = "Late evening";   part = "night"; }
    else if (hour < 11) { salute = "Good morning";   part = "morning"; }
    else if (hour < 14) { salute = "Hello";          part = "afternoon"; }
    else if (hour < 17) { salute = "Good afternoon"; part = "afternoon"; }
    else if (hour < 21) { salute = "Good evening";   part = "evening"; }
    else                { salute = "Evening";        part = "night"; }

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

    return salute + ". " + tail;
  }

  if (greetingEl) {
    greetingEl.textContent = buildGreeting();
  }

  /* ── Compose bar ──────────────────────────────────────────────────
     Send button enables once there's something to send. Submitting
     hands the text off to handleUserMessage (a stub for now). */

  function syncSendState() {
    if (!sendBtn || !input) return;
    sendBtn.disabled = input.value.trim().length === 0;
  }
  if (input) {
    input.addEventListener("input", syncSendState);
  }
  syncSendState();

  function setConversing() {
    root.setAttribute("data-state", "conversing");
  }

  /* Placeholder responder. Wires up in the next pass to:
       1. Compose multi-venue itineraries from window.GUIDE.venues.
       2. Render venue cards on the fly.
       3. Hand off out-of-scope questions to the front desk via
          a tap-to-call card. */
  function handleUserMessage(text) {
    setConversing();
    pushUser(text);
    /* No reply rendered yet — the empty-state is what we're reviewing
       right now. The conversation flow is the next pass. */
  }

  function pushUser(text) {
    const el = document.createElement("div");
    el.className = "msg msg--user";
    el.textContent = text;
    logEl.appendChild(el);
    scrollToCompose();
  }

  function scrollToCompose() {
    /* Wait a frame so the new node has laid out. */
    requestAnimationFrame(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
    });
  }

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

  /* Starter chips just fill the input and submit. */
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
