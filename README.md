# 🐺 Fankaar Digital AI Agency

Autonomous AI Digital Marketing Agency with 23 specialized agents, voice-powered JARVIS interface, campaign engine, billing, and WhatsApp integration.

## 🚀 Quick Start (Local)

```bash
pip install -r requirements.txt
export PYTHONPATH=$PYTHONPATH:$(pwd)/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend
```

Open **http://localhost:8000** to use the JARVIS voice interface.

---

## 🛠️ Deployment (Railway)

### 1. Fork / Connect Repo
Push this repo to GitHub and connect it in [Railway](https://railway.app).

### 2. Add Environment Variables
In Railway Dashboard → Variables, add:

| Variable | Value | Required |
|----------|-------|----------|
| `MOONSHOT_API_KEY` | Your Kimi/Moonshot API key | ✅ Yes |
| `TWILIO_ACCOUNT_SID` | `AC...` (must start with AC) | For WhatsApp |
| `TWILIO_AUTH_TOKEN` | From Twilio Console | For WhatsApp |
| `TWILIO_WHATSAPP_NUMBER` | `+14155238886` | For WhatsApp |
| `OWNER_WHATSAPP_NUMBER` | `+971501006735` | For daily reports |
| `AGENCY_NAME` | `Fankaar Digital` | No |
| `OWNER_NAME` | `Monis` | No |
| `APP_ENV` | `production` | No |

**⚠️ Important:**
- Twilio Account SID **must start with `AC`**. If yours starts with `USd`, it's incorrect — get the real one from [Twilio Console](https://console.twilio.com/).
- The Kimi API key is also your Moonshot key (same service).

### 3. Add Persistent Volume (for database)
Railway Dashboard → Volumes → Add Volume:
- **Mount Path:** `/app/data`
- **Size:** 1GB (or more)

Without this, your database resets on every deploy.

### 4. Custom Domain
Railway Dashboard → Settings → Domains:
- Add `app.fankaar.digital`
- Point your DNS A record to the Railway-provided IP, or CNAME to the Railway domain

---

## 🎙️ JARVIS Voice Interface

The root path (`/`) serves the JARVIS voice command center. Tap the microphone and speak commands like:
- *"Jon, generate the daily report"*
- *"Jon, what's the team status?"*
- *"Jon, assign a task to Sandor"*

---

## 📋 Lead Intake Form

`POST /webhook/intake`

Accepts form data or JSON:
```json
{
  "name": "Client Name",
  "email": "client@example.com",
  "company": "Company LLC",
  "message": "Project details...",
  "budget_range": "5000-10000 AED",
  "service_interest": "Social Media Management"
}
```

Sandor (Sales Director) will auto-qualify the lead via AI.

---

## 🔧 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/agents` | List all 23 agents |
| `POST /api/ceo/message` | Talk to Jon Snow |
| `POST /api/campaigns` | Create campaign |
| `POST /webhook/intake` | Lead form submission |
| `POST /webhook/whatsapp` | Twilio WhatsApp webhook |

Full docs at `/docs` (Swagger UI) or `/redoc`.

---

## 🏗️ Architecture

- **Backend:** FastAPI (Python 3.11)
- **Database:** SQLite (with Railway Volume for persistence)
- **Agents:** 23 autonomous agents with memory + task queue
- **LLM:** Moonshot (Kimi) primary, OpenAI/Anthropic/Ollama fallback
- **Voice:** Web Speech API (browser-based)
- **Worker:** Background asyncio loop for autonomous task execution
- **WhatsApp:** Twilio API for daily reports and owner commands

---

## 📝 License

Built for Fankaar Digital.
