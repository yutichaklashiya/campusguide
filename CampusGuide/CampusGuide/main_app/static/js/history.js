/* =====================================================
   Chat History Sidebar – JavaScript
   Stores Q&A pairs in localStorage AND loads past
   conversations from the database via API.
   Answers are truncated to one line and expand on click.
   ===================================================== */

const HISTORY_KEY = "campusguide_chat_history";

/* ---------- localStorage helpers ---------- */
function getHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY)) || [];
  } catch (_) {
    return [];
  }
}

function saveHistory(history) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
}

/* ---------- Add a Q&A pair ---------- */
function addToHistory(question, answer) {
  const history = getHistory();
  history.unshift({
    q: question,
    a: answer,
    ts: Date.now()
  });
  // Keep last 100 items max
  if (history.length > 100) history.length = 100;
  saveHistory(history);
  renderHistory();
}

/* ---------- Fetch old history from database ---------- */
function fetchDatabaseHistory() {
  // Build the correct URL with language prefix if present
  let historyUrl = "/chat-history/";
  const pathParts = window.location.pathname.split('/');
  if (pathParts.length > 1 && pathParts[1].length === 2) {
    historyUrl = "/" + pathParts[1] + "/chat-history/";
  }

  fetch(historyUrl, {
    method: "GET",
    headers: {
      "X-Requested-With": "XMLHttpRequest"
    }
  })
  .then(response => {
    if (!response.ok) throw new Error("Failed to fetch history");
    return response.json();
  })
  .then(data => {
    if (data.history && data.history.length > 0) {
      mergeDbHistory(data.history);
      renderHistory();
    }
  })
  .catch(err => {
    console.log("History fetch skipped:", err.message);
  });
}

/* ---------- Merge database history with localStorage ---------- */
function mergeDbHistory(dbItems) {
  const localHistory = getHistory();

  // Create a Set of existing question+timestamp combos to avoid duplicates
  const existingKeys = new Set();
  localHistory.forEach(item => {
    existingKeys.add(item.q.trim().toLowerCase() + "|" + item.ts);
  });

  let added = 0;
  dbItems.forEach(dbItem => {
    const key = dbItem.q.trim().toLowerCase() + "|" + dbItem.ts;
    if (!existingKeys.has(key)) {
      // Also check if same question text already exists (fuzzy match)
      const alreadyHasQuestion = localHistory.some(
        local => local.q.trim().toLowerCase() === dbItem.q.trim().toLowerCase()
                 && Math.abs(local.ts - dbItem.ts) < 60000 // within 1 minute
      );
      if (!alreadyHasQuestion) {
        localHistory.push({
          q: dbItem.q,
          a: dbItem.a,
          ts: dbItem.ts
        });
        added++;
      }
    }
  });

  if (added > 0) {
    // Sort by timestamp descending (newest first)
    localHistory.sort((a, b) => b.ts - a.ts);
    // Cap at 100
    if (localHistory.length > 100) localHistory.length = 100;
    saveHistory(localHistory);
  }
}

/* ---------- Render history list ---------- */
function renderHistory() {
  const list = document.getElementById("historyList");
  const emptyMsg = document.getElementById("historyEmpty");
  if (!list) return;

  const history = getHistory();

  // Clear existing items but keep the empty message element
  list.querySelectorAll(".history-item").forEach(el => el.remove());

  if (history.length === 0) {
    if (emptyMsg) emptyMsg.style.display = "block";
    return;
  }

  if (emptyMsg) emptyMsg.style.display = "none";

  history.forEach((item, idx) => {
    const card = document.createElement("div");
    card.className = "history-item";
    card.setAttribute("data-index", idx);

    // Question row
    const qDiv = document.createElement("div");
    qDiv.className = "history-question";

    const qIcon = document.createElement("span");
    qIcon.className = "history-question-icon";
    qIcon.textContent = "\uD83D\uDCAC"; // 💬

    const qText = document.createElement("span");
    qText.className = "history-question-text";
    qText.textContent = item.q;

    qDiv.appendChild(qIcon);
    qDiv.appendChild(qText);

    // Answer row (truncated)
    const aDiv = document.createElement("div");
    aDiv.className = "history-answer";
    aDiv.textContent = item.a;

    // Fade overlay
    const fade = document.createElement("div");
    fade.className = "history-answer-fade";
    aDiv.appendChild(fade);

    // "click to expand" hint
    const hint = document.createElement("div");
    hint.className = "history-expand-hint";
    hint.textContent = "\u25BC click to expand";

    // Timestamp
    const timeDiv = document.createElement("div");
    timeDiv.className = "history-time";
    timeDiv.textContent = formatTime(item.ts);

    card.appendChild(qDiv);
    card.appendChild(aDiv);
    card.appendChild(hint);
    card.appendChild(timeDiv);

    // Click to expand / collapse answer
    card.addEventListener("click", (e) => {
      e.stopPropagation();
      card.classList.toggle("expanded");
    });

    list.appendChild(card);
  });
}

/* ---------- Format timestamp ---------- */
function formatTime(ts) {
  const d = new Date(ts);
  const now = new Date();
  const diffMs = now - d;
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return diffMins + " min ago";

  const diffHrs = Math.floor(diffMins / 60);
  if (diffHrs < 24) return diffHrs + "h ago";

  const diffDays = Math.floor(diffHrs / 24);
  if (diffDays < 7) return diffDays + "d ago";

  // Show date if older
  const day = d.getDate().toString().padStart(2, "0");
  const month = (d.getMonth() + 1).toString().padStart(2, "0");
  return day + "/" + month + " " + d.getHours().toString().padStart(2, "0") + ":" + d.getMinutes().toString().padStart(2, "0");
}

/* ---------- Toggle sidebar ---------- */
function toggleHistorySidebar() {
  const sidebar = document.getElementById("historySidebar");
  const btn = document.getElementById("historyToggleBtn");

  if (!sidebar) return;

  const isOpen = sidebar.classList.toggle("open");
  if (btn) btn.classList.toggle("active", isOpen);

  // Re-render when opening
  if (isOpen) renderHistory();
}

/* ---------- Clear all history ---------- */
function clearChatHistory() {
  if (!confirm("Are you sure you want to clear all chat history?")) return;
  localStorage.removeItem(HISTORY_KEY);
  renderHistory();
}

/* ---------- Init on page load ---------- */
document.addEventListener("DOMContentLoaded", () => {
  // First render whatever is in localStorage
  renderHistory();
  // Then fetch old history from database and merge
  fetchDatabaseHistory();
});
