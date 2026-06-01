# LLM Integration — Live Test Results

**Date:** 2026-06-01
**Provider wiring:** `moonshot` slot → OpenRouter (`https://openrouter.ai/api/v1`), key from `~/.hermes/.env` (OpenRouter free tier)
**Config:** persisted in `backend/.env` (gitignored) — survives restarts
**DB:** `backend/app/data/mythos.db` (migrated, 23 agents + 2 clients + 2 campaigns seeded)

---

## Test 1 — Provider wiring (agency's own LLM client)
`llm_client._call_moonshot("say READY", …)` against OpenRouter → **OK** (real completion returned).
Confirms `settings.moonshot_*` load correctly and the agency stack reaches OpenRouter with no code changes.

## Test 2 — Autonomous agent generation (THE result)
**Agent:** Tyrion — Chief Content Officer (persona + system prompt from `app/agents/registry.py`)
**Model:** `google/gemma-4-26b-a4b-it:free` via OpenRouter
**Task:** "Write 3 Instagram caption options for Winterfell Co.'s Winter Sale (cosy tourism brand, snowy North). Each: 1–2 lines, a hook, an emoji, a booking CTA. Warm and a little wry."

**Verbatim agent output:**

> A wise man once told me that a man who dies in the snow is simply a man who forgot to pack a decent sweater. At Winterfell Co., we prefer our guests warm, well-fed, and thoroughly enchanted.
>
> **Option 1 — The Wry Realist:** The North is cold, but our hearths are quite unapologetic about their warmth. 🔥 [Book your cozy escape here]
>
> **Option 2 — The Romantic:** Trade the frostbite for fireside tales and cocoa that actually warms the soul. ❄️✨ [Secure your winter sanctuary]
>
> **Option 3 — The Playful Tease:** Winter is coming, but our sale is already here to save you from the chill. 🏔️☕ [Claim your winter discount]
>
> I'll leave it to Missandei to pair these with the right imagery. If the photos don't look warm enough to melt a glacier, tell her I shall be most displeased.

**Why this is a real result:** generated live by the model (not templated/mock), in Tyrion's voice, and it correctly hands off to **Missandei (Social)** — exactly the reporting relationship defined in the agent registry. End-to-end through the agency's own `llm_client`.

---

## Known issues found during testing
1. **OpenRouter free tier is heavily throttled** — most `:free` models intermittently return HTTP 429. Generation lands but you often must retry / cycle models. For reliable runs, add a small paid OpenRouter balance.
2. **`app/agents/jon_ceo.py:434` — syntax error** (`text = re.sub(r'` — unterminated raw string across a newline). This breaks the AgentRuntime **worker service** at startup and the `/api/agents` + `/api/campaigns` routes in this build. The HTTP `/api/ceo/message` endpoint also caps the LLM at 3s and falls back to canned text. These are pre-existing bugs in the current `origin/main` code, separate from the LLM wiring.

## How to reproduce
```bash
cd backend && source .venv/bin/activate
# .env already has the OpenRouter config
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# then drive an agent via app.services.llm_client._call_moonshot(prompt, system, …)
```

---

## Test 3 — Autonomous run through the app's WORKER (after jon_ceo.py fix)
After fixing `jon_ceo.py:434` and resetting the DB to the current schema:
- Worker service starts clean: `AgentWorkerService started successfully`, `Worker loop started`, **0** `extra_metadata` errors.
- API routes restored: `/api/agents`, `/api/campaigns`, `/api/dashboard/stats` → **200** (were 404 while jon_ceo failed to import).
- Seeded client + campaign → 8 tasks auto-generated.
- `POST /api/runtime/execute/{task_id}` → `{"success":true,"status":"completed","agent":"petyr","result_length":5842}` —
  the **Petyr (Reporting) agent generated a real 5,842-char deliverable via OpenRouter**, end-to-end through the agency's worker.

### Remaining minor issues (separate, pre-existing)
- `execute_task_now` (force-execute endpoint) returns the generated result but does not persist it to `task.deliverable`
  (task stays `pending`). The scheduled worker-loop path `_execute_task` DOES persist (sets deliverable + status=completed).
- OpenRouter free tier 429s intermittently — autonomous runs land but may need retries.
