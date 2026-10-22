/**
 * SchedulAI Frontend Application Logic — Minimal ChatGPT-Style Socratic Tutor Frontend
 */

const API_BASE = "";

// State
let currentSessionId = localStorage.getItem("schedulai_active_session") || null;
let isGenerating = false;

// DOM Elements
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebar-toggle");
const btnNewChat = document.getElementById("btn-new-chat");
const sessionList = document.getElementById("session-list");
const chatStream = document.getElementById("chat-stream");
const welcomeScreen = document.getElementById("welcome-screen");
const messagesList = document.getElementById("messages-list");
const scrollBottom = document.getElementById("scroll-bottom");
const userInput = document.getElementById("user-input");
const btnSend = document.getElementById("btn-send");
const chatTitle = document.getElementById("chat-title");
const chatStatus = document.getElementById("chat-status");

// Initialization
document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  await loadSessions();

  if (currentSessionId) {
    await loadSessionHistory(currentSessionId);
  } else {
    showWelcomeScreen();
  }
});

function setupEventListeners() {
  // Sidebar Toggle
  sidebarToggle.addEventListener("click", () => {
    sidebar.classList.toggle("collapsed");
  });

  // New Chat
  btnNewChat.addEventListener("click", startNewChat);

  // Input Handling
  userInput.addEventListener("input", () => {
    // Auto-expand textarea
    userInput.style.height = "auto";
    userInput.style.height = Math.min(userInput.scrollHeight, 180) + "px";

    // Enable / disable send button
    btnSend.disabled = !userInput.value.trim() || isGenerating;
  });

  userInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (!btnSend.disabled) {
        handleSendMessage();
      }
    }
  });

  btnSend.addEventListener("click", handleSendMessage);

  // Starter card prompts
  document.querySelectorAll(".starter-card").forEach((card) => {
    card.addEventListener("click", () => {
      const prompt = card.getAttribute("data-prompt");
      if (prompt) {
        userInput.value = prompt;
        userInput.dispatchEvent(new Event("input"));
        handleSendMessage();
      }
    });
  });
}

async function startNewChat() {
  if (isGenerating) return;
  try {
    const res = await fetch(`${API_BASE}/api/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "New Conversation", topic: "Fundamentals" })
    });
    if (res.ok) {
      const data = await res.json();
      currentSessionId = data.session_id;
      localStorage.setItem("schedulai_active_session", currentSessionId);
      chatTitle.textContent = "New Conversation";
      messagesList.innerHTML = "";
      showWelcomeScreen();
      await loadSessions();
      userInput.focus();
    }
  } catch (e) {
    console.error("Failed to create new session:", e);
  }
}

async function loadSessions() {
  try {
    const res = await fetch(`${API_BASE}/api/sessions`);
    if (!res.ok) return;
    const sessions = await res.json();

    sessionList.innerHTML = "";
    if (sessions.length === 0) {
      sessionList.innerHTML = '<div class="empty-sessions">No saved chats</div>';
      return;
    }

    sessions.forEach((s) => {
      const item = document.createElement("div");
      item.className = `session-item ${s.session_id === currentSessionId ? "active" : ""}`;
      item.title = s.title || "Untitled";

      const titleSpan = document.createElement("span");
      titleSpan.textContent = s.title || "Untitled Session";
      titleSpan.style.overflow = "hidden";
      titleSpan.style.textOverflow = "ellipsis";

      const delBtn = document.createElement("button");
      delBtn.className = "btn-del-session";
      delBtn.innerHTML = "&times;";
      delBtn.title = "Delete Chat";
      delBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await deleteSession(s.session_id);
      });

      item.appendChild(titleSpan);
      item.appendChild(delBtn);

      item.addEventListener("click", async () => {
        if (s.session_id !== currentSessionId) {
          currentSessionId = s.session_id;
          localStorage.setItem("schedulai_active_session", currentSessionId);
          await loadSessionHistory(s.session_id);
          await loadSessions();
        }
      });

      sessionList.appendChild(item);
    });
  } catch (e) {
    console.error("Failed to load sessions:", e);
  }
}

async function deleteSession(sessionId) {
  try {
    const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, { method: "DELETE" });
    if (res.ok) {
      if (currentSessionId === sessionId) {
        currentSessionId = null;
        localStorage.removeItem("schedulai_active_session");
        messagesList.innerHTML = "";
        showWelcomeScreen();
      }
      await loadSessions();
    }
  } catch (e) {
    console.error("Failed to delete session:", e);
  }
}

async function loadSessionHistory(sessionId) {
  try {
    const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`);
    if (!res.ok) {
      showWelcomeScreen();
      return;
    }
    const data = await res.json();
    chatTitle.textContent = data.title || "SchedulAI";

    messagesList.innerHTML = "";
    if (!data.messages || data.messages.length === 0) {
      showWelcomeScreen();
    } else {
      hideWelcomeScreen();
      data.messages.forEach((msg) => {
        let structured = null;
        if (msg.structured_json) {
          try {
            structured = JSON.parse(msg.structured_json);
          } catch (_) {}
        }
        appendMessage(msg.role, msg.content, structured);
      });
      scrollToBottom();
    }
  } catch (e) {
    console.error("Failed to load session history:", e);
    showWelcomeScreen();
  }
}

async function handleSendMessage() {
  const text = userInput.value.trim();
  if (!text || isGenerating) return;

  hideWelcomeScreen();
  appendMessage("user", text);
  userInput.value = "";
  userInput.style.height = "auto";
  btnSend.disabled = true;
  isGenerating = true;
  chatStatus.textContent = "Thinking...";

  const typingElem = showTypingIndicator();

  try {
    const payload = {
      session_id: currentSessionId,
      message: text
    };

    const res = await fetch(`${API_BASE}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    removeTypingIndicator(typingElem);

    if (!res.ok) {
      appendMessage("assistant", "An error occurred communicating with SchedulAI. Please check backend connection.");
      return;
    }

    const data = await res.json();
    currentSessionId = data.session_id;
    localStorage.setItem("schedulai_active_session", currentSessionId);

    appendMessage("assistant", data.message, data);
    scrollToBottom();
    await loadSessions();
  } catch (e) {
    removeTypingIndicator(typingElem);
    appendMessage("assistant", "Network error: Unable to reach SchedulAI server.");
  } finally {
    isGenerating = false;
    btnSend.disabled = !userInput.value.trim();
    chatStatus.textContent = "Ready";
  }
}

function appendMessage(role, text, structuredData = null) {
  const row = document.createElement("div");
  row.className = `msg-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = "⚡";

  const body = document.createElement("div");
  body.className = "msg-body";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = formatMarkdown(text);
  body.appendChild(bubble);

  // Gantt chart block if available
  if (structuredData && structuredData.gantt_chart_ascii) {
    const ganttPre = document.createElement("pre");
    ganttPre.className = "ascii-gantt-block";
    ganttPre.textContent = structuredData.gantt_chart_ascii;
    body.appendChild(ganttPre);
  }

  row.appendChild(avatar);
  row.appendChild(body);
  messagesList.appendChild(row);
  scrollToBottom();
}

function showTypingIndicator() {
  const row = document.createElement("div");
  row.className = "msg-row assistant typing";
  row.innerHTML = `
    <div class="msg-avatar">⚡</div>
    <div class="msg-body">
      <div class="msg-bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    </div>
  `;
  messagesList.appendChild(row);
  scrollToBottom();
  return row;
}

function removeTypingIndicator(elem) {
  if (elem && elem.parentNode) {
    elem.parentNode.removeChild(elem);
  }
}

function showWelcomeScreen() {
  welcomeScreen.style.display = "flex";
}

function hideWelcomeScreen() {
  welcomeScreen.style.display = "none";
}

function scrollToBottom() {
  scrollBottom.scrollIntoView({ behavior: "smooth" });
}

function formatMarkdown(text) {
  if (!text) return "";

  let s = escapeHtml(text);

  // Remove lines with raw hash tags
  s = s.replace(/^[#]{1,6}\s*(.*)$/gm, "<h3>$1</h3>");

  // Bold & Italic
  s = s.replace(/\*\*\*(.*?)\*\*\*/g, "<strong><em>$1</em></strong>");
  s = s.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/\*(.*?)\*/g, "<em>$1</em>");

  // Inline Math $...$
  s = s.replace(/\$([^\$]+)\$/g, "<code class='math-code'>$1</code>");

  // Inline code `code`
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Blockquotes > quote
  s = s.replace(/^>\s*(.*)$/gm, "<blockquote>$1</blockquote>");

  // Bullet points
  s = s.replace(/^\*\s+(.*)$/gm, "<li>$1</li>");
  s = s.replace(/^-\s+(.*)$/gm, "<li>$1</li>");

  // Wrap groups of <li> into <ul>
  s = s.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");

  // Tables
  if (s.includes("|")) {
    const lines = s.split("\n");
    let inTable = false;
    let tableHtml = "<table>";

    const formattedLines = [];
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i].trim();
      if (line.startsWith("|") && line.endsWith("|")) {
        // Skip separator row like | :--- | :--- |
        if (line.replace(/[\s|:\-]/g, "") === "") {
          continue;
        }
        if (!inTable) {
          inTable = true;
          tableHtml = "<table>";
        }
        const cells = line.split("|").filter((c, idx, arr) => idx > 0 && idx < arr.length - 1);
        const tag = tableHtml.includes("<tbody>") ? "td" : "th";
        const rowContent = cells.map((c) => `<${tag}>${c.trim()}</${tag}>`).join("");

        if (!tableHtml.includes("<tbody>") && tag === "th") {
          tableHtml += `<thead><tr>${rowContent}</tr></thead><tbody>`;
        } else {
          tableHtml += `<tr>${rowContent}</tr>`;
        }
      } else {
        if (inTable) {
          inTable = false;
          tableHtml += "</tbody></table>";
          formattedLines.push(tableHtml);
        }
        formattedLines.push(line);
      }
    }
    if (inTable) {
      tableHtml += "</tbody></table>";
      formattedLines.push(tableHtml);
    }
    s = formattedLines.join("\n");
  }

  // Newlines to <br> where not in table or list
  s = s.replace(/\n\n/g, "<br><br>").replace(/\n/g, "<br>");
  return s;
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
