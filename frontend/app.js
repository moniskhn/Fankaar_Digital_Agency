/**
 * Fankaar Digital — Jarvis Command Interface v4
 * Cache-bust: 2026-05-20-0025
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
        if (tabId === 'clients') loadClients();
        if (tabId === 'schedule') loadSchedule();
        if (tabId === 'deliverables') loadDeliverables();
    });
});

// ── Voice Output (TTS) — Jarvis Mode ─────────────────────
let voiceEnabled = true;
let jarvisVoice = null;

function initVoice() {
    if (!window.speechSynthesis) return;
    const voices = window.speechSynthesis.getVoices();
    // Prefer a deep male voice for Jarvis feel
    jarvisVoice = voices.find(v => v.name.toLowerCase().includes('male') && v.lang.startsWith('en'))
        || voices.find(v => v.name.toLowerCase().includes('daniel') || v.name.toLowerCase().includes('tom'))
        || voices.find(v => v.lang === 'en-US' || v.lang === 'en-GB')
        || voices[0];
}

if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = initVoice;
    initVoice();
}

function speak(text) {
    if (!voiceEnabled || !window.speechSynthesis) return;
    // Strip emojis and markdown for cleaner speech
    const clean = text.replace(/[\u{1F300}-\u{1F9FF}]/gu, '').replace(/[📊⚡👤🎨📅💬✅🔥⏱️🎙️›]/g, '').trim();
    if (!clean) return;

    window.speechSynthesis.cancel(); // stop any previous speech
    const utter = new SpeechSynthesisUtterance(clean);
    utter.voice = jarvisVoice;
    utter.pitch = 0.85;   // deeper
    utter.rate = 1.05;    // slightly faster, more crisp
    utter.volume = 1.0;
    window.speechSynthesis.speak(utter);
}

const voiceToggle = document.getElementById('voice-toggle');
if (voiceToggle) {
    voiceToggle.addEventListener('click', () => {
        voiceEnabled = !voiceEnabled;
        voiceToggle.textContent = voiceEnabled ? '🔊' : '🔇';
        voiceToggle.style.opacity = voiceEnabled ? '1' : '0.4';
        if (!voiceEnabled) window.speechSynthesis.cancel();
    });
}

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
        const reply = data.response || 'Jon received your message.';
        addMessage(reply, 'jarvis');
        speak(reply); // 🔊 Jarvis speaks
    } catch (err) {
        let msg;
        if (err.name === 'AbortError') {
            msg = "⏱️ Jon took too long to respond. He's busy — try again shortly.";
        } else {
            msg = "Connection error. API may be restarting. Try again.";
        }
        addMessage(msg, 'system');
        speak(msg);
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

// ── Clients ────────────────────────────────────────────────
let clientsCache = null;
const clientList = document.getElementById('client-list');
const clientForm = document.getElementById('client-form');
const addClientBtn = document.getElementById('add-client-btn');
const saveClientBtn = document.getElementById('save-client');
const cancelClientBtn = document.getElementById('cancel-client');

async function loadClients() {
    if (clientsCache) {
        renderClients(clientsCache);
        return;
    }
    clientList.innerHTML = '<div class="loading">Loading clients...</div>';

    try {
        const response = await fetchWithTimeout(`${API_BASE}/api/clients`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        clientsCache = data;
        renderClients(data);
    } catch (err) {
        let msg = "Error loading clients.";
        if (err.name === 'AbortError') msg = "⏱️ Timed out. Click Clients tab again to retry.";
        clientList.innerHTML = `<div class="loading">${msg}</div>`;
    }
}

function renderClients(clients) {
    if (!clients || clients.length === 0) {
        clientList.innerHTML = '<div class="loading">No clients yet. Click + Add Client to create one.</div>';
        return;
    }
    const html = clients.map(c => `
        <div class="client-card">
            <div class="client-name">${escapeHtml(c.name)}</div>
            <div class="client-meta">${escapeHtml(c.industry || '')} · ${escapeHtml(c.region || '')} · ${escapeHtml(c.contact_email || '')}</div>
            <span class="client-status">${escapeHtml(c.status || 'active')}</span>
        </div>
    `).join('');
    clientList.innerHTML = html;
}

addClientBtn.addEventListener('click', () => {
    clientForm.classList.remove('hidden');
    clientList.style.display = 'none';
    addClientBtn.style.display = 'none';
});

cancelClientBtn.addEventListener('click', () => {
    clientForm.classList.add('hidden');
    clientList.style.display = 'flex';
    addClientBtn.style.display = 'inline-block';
});

saveClientBtn.addEventListener('click', async () => {
    const name = document.getElementById('client-name').value.trim();
    const industry = document.getElementById('client-industry').value.trim();
    const region = document.getElementById('client-region').value.trim();
    const contact = document.getElementById('client-contact').value.trim();

    if (!name) {
        alert('Company name is required');
        return;
    }

    try {
        const response = await fetchWithTimeout(`${API_BASE}/api/clients`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name, industry, region,
                contact_email: contact,
                contact_name: '',
                timezone: 'Asia/Dubai',
                target_audience: '',
                brand_voice: '',
                goals: [],
                budget_range: '',
                notes: ''
            })
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        // Reset form and reload
        document.getElementById('client-name').value = '';
        document.getElementById('client-industry').value = '';
        document.getElementById('client-region').value = '';
        document.getElementById('client-contact').value = '';
        clientForm.classList.add('hidden');
        clientList.style.display = 'flex';
        addClientBtn.style.display = 'inline-block';
        clientsCache = null;
        loadClients();
    } catch (err) {
        alert('Failed to save client: ' + (err.message || 'Unknown error'));
    }
});

// ── Schedule ───────────────────────────────────────────────
let scheduleCache = null;
const scheduleContent = document.getElementById('schedule-content');

async function loadSchedule() {
    if (scheduleCache) {
        renderSchedule(scheduleCache);
        return;
    }
    scheduleContent.innerHTML = '<div class="loading">Loading schedule...</div>';

    try {
        const response = await fetchWithTimeout(`${API_BASE}/api/calendar/upcoming?hours=168`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        scheduleCache = data;
        renderSchedule(data);
    } catch (err) {
        let msg = "Error loading schedule.";
        if (err.name === 'AbortError') msg = "⏱️ Timed out. Click Schedule tab again to retry.";
        scheduleContent.innerHTML = `<div class="loading">${msg}</div>`;
    }
}

function renderSchedule(posts) {
    if (!posts || posts.length === 0) {
        scheduleContent.innerHTML = '<div class="loading">No upcoming posts scheduled. Create a campaign and generate a calendar to see content here.</div>';
        return;
    }
    const html = posts.map(p => {
        const time = new Date(p.scheduled_time).toLocaleString('en-US', {
            weekday: 'short', month: 'short', day: 'numeric',
            hour: '2-digit', minute: '2-digit'
        });
        return `
        <div class="schedule-item">
            <div class="schedule-time">${escapeHtml(time)}</div>
            <div class="schedule-text">${escapeHtml(p.content_text || 'Scheduled post')}</div>
            <div class="schedule-platform">${escapeHtml(p.platform || 'general')}</div>
        </div>
        `;
    }).join('');
    scheduleContent.innerHTML = html;
}

// ── Deliverables ───────────────────────────────────────────
let deliverablesCache = null;
const deliverablesContent = document.getElementById('deliverables-content');

async function loadDeliverables() {
    if (deliverablesCache) {
        renderDeliverables(deliverablesCache);
        return;
    }
    deliverablesContent.innerHTML = '<div class="loading">Loading deliverables...</div>';

    try {
        // Try to get campaign tasks as deliverables
        const response = await fetchWithTimeout(`${API_BASE}/api/campaigns`);
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const campaigns = await response.json();

        // Fetch tasks for each campaign
        const allTasks = [];
        for (const camp of campaigns.slice(0, 5)) {
            try {
                const tr = await fetchWithTimeout(`${API_BASE}/api/campaigns/${camp.id}/tasks`);
                if (tr.ok) {
                    const tasks = await tr.json();
                    tasks.forEach(t => allTasks.push({
                        title: t.title,
                        campaign: camp.campaign_name || camp.name,
                        status: t.status,
                        assignee: t.assigned_to,
                        deliverable: t.deliverable || 'Pending'
                    }));
                }
            } catch (e) { /* ignore per-campaign errors */ }
        }

        deliverablesCache = allTasks;
        renderDeliverables(allTasks);
    } catch (err) {
        let msg = "Error loading deliverables.";
        if (err.name === 'AbortError') msg = "⏱️ Timed out. Click Deliverables tab again to retry.";
        deliverablesContent.innerHTML = `<div class="loading">${msg}</div>`;
    }
}

function renderDeliverables(tasks) {
    if (!tasks || tasks.length === 0) {
        deliverablesContent.innerHTML = '<div class="loading">No deliverables yet. Create a campaign and assign tasks with deliverables to see them here.</div>';
        return;
    }
    const statusClass = s => {
        if (s === 'completed' || s === 'done') return 'status-done';
        if (s === 'blocked' || s === 'failed') return 'status-blocked';
        return 'status-pending';
    };
    const html = tasks.map(t => `
        <div class="deliverable-item">
            <div class="deliverable-title">${escapeHtml(t.title)}</div>
            <div class="deliverable-meta">${escapeHtml(t.campaign)} · ${escapeHtml(t.assignee)}</div>
            <span class="deliverable-status ${statusClass(t.status)}">${escapeHtml(t.status)}</span>
        </div>
    `).join('');
    deliverablesContent.innerHTML = html;
}

// ── Random Stats ───────────────────────────────────────────
setInterval(() => {
    document.getElementById('cpu-load').textContent = (Math.random() * 5 + 2).toFixed(1) + '%';
}, 3000);

// ── Init ───────────────────────────────────────────────────
// Don't auto-load report/agents — only load when tab is clicked
// This prevents the page from hanging on startup
