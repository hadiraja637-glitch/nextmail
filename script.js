let currentEmail = null, expiresAt = null, timerInterval = null;

async function api(path, options = {}) {
    const headers = { ...(options.headers || {}), "Content-Type": "application/json" };
    const r = await fetch("/api" + path, { ...options, headers });
    const d = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(d.detail || "Request failed");
    return d;
}

function renderTimer() {
    const el = document.getElementById("timer");
    if (!el || !expiresAt) return;
    const left = Math.max(0, new Date(expiresAt) - Date.now()), s = Math.floor(left / 1000);
    el.textContent = String(Math.floor(s / 3600)).padStart(2, "0") + ":" + String(Math.floor(s % 3600 / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
    if (left <= 0) {
        clearInterval(timerInterval);
        currentEmail = null;
        const i = document.getElementById("emailInput");
        if (i) i.value = "Expired — Generate New Email";
    }
}

function startTimer(x) {
    expiresAt = x;
    clearInterval(timerInterval);
    renderTimer();
    timerInterval = setInterval(renderTimer, 1000);
}

async function generateEmail() {
    const b = document.querySelector(".new-btn");
    if (b) b.disabled = true;
    try {
        const d = await api("/generate", { method: "GET" });
        currentEmail = d.email;
        const emailInput = document.getElementById("emailInput");
        if (emailInput) emailInput.value = currentEmail;
        startTimer(new Date(Date.now() + 10 * 60 * 1000).toISOString());
        loadInbox();
    } catch (e) {
        console.error(e);
    } finally {
        if (b) b.disabled = false;
    }
}

async function copyEmail() {
    if (!currentEmail) return;
    await navigator.clipboard.writeText(currentEmail);
    const b = document.querySelector(".copy-btn");
    if (b) {
        b.innerText = "Copied!";
        setTimeout(() => b.innerText = "Copy", 1500);
    }
}

async function loadInbox() {
    if (!currentEmail) return;
    try {
        const d = await api("/inbox/" + encodeURIComponent(currentEmail));
        renderInbox(d.messages || []);
    } catch (e) {}
}

function renderInbox(messages) {
    let box = document.getElementById("inbox");
    if (!box) return;
    box.innerHTML = messages.length ? messages.map(m => `
        <div class="email-item" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); padding: 12px; margin-bottom: 10px; border-radius: 8px;">
            <div style="color: #00f2fe; font-size: 13px; margin-bottom: 4px;"><b>From:</b> ${escapeHtml(m.sender)}</div>
            <div style="color: #fff; font-size: 14px; font-weight: 600; margin-bottom: 6px;"><b>Subject:</b> ${escapeHtml(m.subject)}</div>
            <div style="color: #94a3b8; font-size: 13px;">${escapeHtml(m.body)}</div>
        </div>
    `).join("") : "<p style='color: #94a3b8; text-align: center; padding: 20px;'>No messages yet. Waiting for incoming emails...</p>";
}

function escapeHtml(v) {
    return String(v).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

document.addEventListener("DOMContentLoaded", () => {
    const b = document.querySelector(".new-btn");
    if (b) b.addEventListener("click", generateEmail);
    generateEmail();
});
