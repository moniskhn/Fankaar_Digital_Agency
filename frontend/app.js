/**
 * Fankaar Digital — Jarvis Command Interface v3
 * Cache-bust: 2026-05-19-2350
 */

const API_BASE = '';
const FETCH_TIMEOUT = 5000; // 5 seconds max — no hanging

// ── Helpers ────────────────────────────────────────────────
async function fetchWithTimeout(url, options = {}) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
    try {
        const response = await fetch(url, { ...options, signal: controller.signal });
        clearTimeout(id);
        return response;
    } catch (err) {
        clearTimeout(id);
        throw err;
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ── DOM Elements ───────────────────────────────────────────
const tabBtns = document.querySelectorAll('.tab-btn');
const tabPanels = document.querySelectorAll('.tab-panel');
const chatMessages = document.getElementById('chat-messages');
const textInput = document.getElementById('text-input');
const sendBtn = document.getElementById('send-btn');
const micBtn = document.getElementById('mic-btn');
const reportContent = document.getElementById('report-content');
const refreshReportBtn = document.getElementById('refresh-report');
const reportDate = document.getElementById('report-date');
const agentGrid = document.getElementById('agent-grid');

// ── Tab Switching ──────────────────────────────────────────
tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        const tabId = btn.dataset.tab;
        tabBtns.forEach(b => b.classList.remove('active'));
        tabPanels.forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab-${tabId}`).classList.add('active');

        if (tabId === 'report') loadDailyReport();
        if (tabId === 'agents') loadAgents();
    });
});

// ── Chat ───────────────────────────────────────────────────
function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `message ${sender}`;
    const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    div.innerHTML = `<p>${escapeHtml(text)}</p><span class="timestamp">${time}</span>`;
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

async function sendMessage(text) {
    if (!text.trim()) return;
    addMessage(text, 'user');
    textInput.value = '';

    try {
        const response = await fetchWithTimeout(`${API_BASE}/api/ceo/message`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        addMessage(data.response || 'Jon received your message.', 'jarvis');
    } catch (err) {
        if (err.name === 'AbortError') {
            addMessage("⏱️ Jon took too long to respond. He's busy — try again shortly.", 'system');
        } else {
            addMessage("Connection error. API may be restarting. Try again.", 'system');
        }
    }
}

textInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(textInput.value);
    }
});

sendBtn.addEventListener('click', () => sendMessage(textInput.value));

// ── Voice Recognition ──────────────────────────────────────
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'en-US';
    recognition.interimResults = false;

    recognition.onstart = () => {
        micBtn.classList.add('listening');
        addMessage("🎙️ Listening...", 'system');
    };

    recognition.onresult = event => {
        const command = event.results[0][0].transcript;
        addMessage(`🎙️ "${command}"`, 'system');
        sendMessage(command);
    };

    recognition.onend = () => micBtn.classList.remove('listening');
    recognition.onerror = () => {
        micBtn.classList.remove('listening');
        addMessage("Voice recognition error. Try typing instead.", 'system');
    };
} else {
    micBtn.style.display = 'none';
}

micBtn.addEventListener('click', () => {
    if (recognition) recognition.start();
});

// ── Daily Report ───────────────────────────────────────────
let reportCache = null;

async function loadDailyReport() {
    if (reportCache) {
        renderReport(reportCache);
        return;
    }
    reportContent.innerHTML = '<div class="loading">Generating report from Jon...</div>';
    reportDate.textContent = new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });

    try {
        const response = await fetchWithTimeout(`${API_BASE}/api/ceo/daily-report`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        reportCache = data;
        renderReport(data);
    } catch (err) {
        let msg = "Jon is compiling the report. Try again in a moment.";
        if (err.name === 'AbortError') {
            msg = "⏱️ Report generation timed out. The AI backend is warming up — click Refresh to try again.";
        }
        reportContent.innerHTML = `
            <div class="report-section">
                <h3>⚠️ Report Unavailable</h3>
                <p>${msg}</p>
                <p style="margin-top:10px; font-size:0.8rem; opacity:0.5;">${escapeHtml(err.message || '')}</p>
            </div>`;
    }
}

function renderReport(data) {
    const sections = [];

    if (data.summary) {
        sections.push(`<div class="report-section"><h3>📋 Executive Summary</h3><p>${escapeHtml(data.summary)}</p></div>`);
    }

    if (data.agent_updates?.length) {
        const agentHtml = data.agent_updates.map(u =>
            `<li><strong>${escapeHtml(u.agent_name)}</strong> — ${u.completed?.length || 0} done, ${u.in_progress?.length || 0} in progress${u.notes ? ` · ${escapeHtml(u.notes)}` : ''}</li>`
        ).join('');
        sections.push(`<div class="report-section"><h3>⚡ Agent Standup</h3><ul>${agentHtml}</ul></div>`);
    }

    if (data.campaigns?.length) {
        const campHtml = data.campaigns.map(c =>
            `<li><strong>${escapeHtml(c.campaign_name)}</strong> — ${c.status} (${c.progress_pct?.toFixed?.(0) || 0}%)${c.highlight ? ` · ${escapeHtml(c.highlight)}` : ''}</li>`
        ).join('');
        sections.push(`<div class="report-section"><h3>🚀 Campaigns</h3><ul>${campHtml}</ul></div>`);
    }

    if (data.tomorrow_priorities?.length) {
        const priHtml = data.tomorrow_priorities.map(p => `<li>${escapeHtml(p)}</li>`).join('');
        sections.push(`<div class="report-section"><h3>📌 Tomorrow's Priorities</h3><ul>${priHtml}</ul></div>`);
    }

    if (data.decisions_made?.length) {
        const decHtml = data.decisions_made.map(d => `<li>${escapeHtml(d)}</li>`).join('');
        sections.push(`<div class="report-section"><h3>✅ Decisions</h3><ul>${decHtml}</ul></div>`);
    }

    if (data.issues_flags?.length) {
        const flagHtml = data.issues_flags.map(f => `<li>${escapeHtml(f)}</li>`).join('');
        sections.push(`<div class="report-section"><h3>⚠️ Issues & Alerts</h3><ul>${flagHtml}</ul></div>`);
    }

    if (sections.length === 0) {
        sections.push(`<div class="report-section"><h3>📊 Report</h3><p>No data available yet. Start running campaigns to generate reports.</p></div>`);
    }

    reportContent.innerHTML = sections.join('');
}

refreshReportBtn.addEventListener('click', () => {
    reportCache = null;
    loadDailyReport();
});

// ── Agents ─────────────────────────────────────────────────
let agentsCache = null;

async function loadAgents() {
    if (agentsCache) {
        renderAgents(agentsCache);
        return;
    }
    agentGrid.innerHTML = '<div class="loading">Loading agent roster...</div>';

    try {
        const response = await fetchWithTimeout(`${API_BASE}/api/agents`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        agentsCache = data;
        renderAgents(data);
    } catch (err) {
        let msg = "Error loading agents.";
        if (err.name === 'AbortError') msg = "⏱️ Agent roster timed out. The backend is warming up — click the Agents tab again to retry.";
        agentGrid.innerHTML = `<div class="loading">${msg}</div>`;
    }
}

function renderAgents(agents) {
    const statusClass = s => {
        if (s === 'active' || s === 'online') return 'active';
        if (s === 'busy' || s === 'working') return 'busy';
        return 'idle';
    };

    const html = agents.map(a => `
        <div class="agent-card">
            <div class="agent-name">${escapeHtml(a.name)}</div>
            <div class="agent-role">${escapeHtml(a.role || 'Agent')}</div>
            <span class="agent-status ${statusClass(a.status)}">${escapeHtml(a.status || 'idle')}</span>
        </div>
    `).join('');

    agentGrid.innerHTML = html;
    document.getElementById('agent-total').textContent = agents.length;
    document.getElementById('agent-count').textContent = agents.length;
}

// ── Random Stats ───────────────────────────────────────────
setInterval(() => {
    document.getElementById('cpu-load').textContent = (Math.random() * 5 + 2).toFixed(1) + '%';
}, 3000);

// ── Init ───────────────────────────────────────────────────
// Don't auto-load report/agents — only load when tab is clicked
// This prevents the page from hanging on startup
