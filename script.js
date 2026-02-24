(function () {
  function byIds(ids) {
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) return el;
    }
    return null;
  }

  function safeText(el, txt) {
    if (!el) return;
    el.textContent = txt;
  }

  function addLine(log, cls, txt) {
    if (!log) return;
    const d = document.createElement("div");
    d.className = cls;
    d.textContent = txt;
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  }

  document.addEventListener("DOMContentLoaded", () => {

    // Accept multiple historic IDs so we never crash again
    const input = byIds(["input", "user-input", "message", "text"]);
    const sendBtn = byIds(["send", "send-btn", "sendBtn", "send-button"]);
    const status = byIds(["status", "banner", "footer"]);
    const log = byIds(["log", "chat-window", "chat", "output"]);

    if (!input || !sendBtn) {
      console.error("SafeSpace UI mismatch: missing input or send button element.");
      safeText(status, "UI mismatch: missing #input or #send. Running repair is required.");
      return; // DO NOT crash
    }

    safeText(status, "SafeSpace is present with you.");
    addLine(log, "bot", "SafeSpace is present with you.");

    async function sendMessage() {
      const text = (input.value || "").trim();
      if (!text) return;

      addLine(log, "me", "You: " + text);
      input.value = "";

      try {
        const resp = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text })
        });

        if (!resp.ok) {
          const t = await resp.text();
          throw new Error("HTTP " + resp.status + ": " + t);
        }

        const data = await resp.json();
        addLine(log, "bot", "SafeSpace: " + (data.reply ?? "(no reply)"));
      } catch (e) {
        console.error(e);
        addLine(log, "bot", "SafeSpace bridge error (check server window).");
      }
    }

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") sendMessage();
    });

  });
})();
