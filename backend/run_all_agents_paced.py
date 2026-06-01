"""Paced, resumable all-agents runner — respects OpenRouter free-tier limits.
Keeps results in agent_state.json; rewrites agent-test-results.md as each lands."""
import asyncio, json, os, time
from app.agents.registry import get_all_agents
from app.core.config import settings
from app.services.llm_client import llm_client
from run_all_agents import TASKS, DEFAULT, MODELS, content_of

STATE = "agent_state.json"
MAX_ROUNDS = 30
BACKOFF = 18  # seconds between attempts (gentle on the free tier)

def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {}

def save_state(s):
    json.dump(s, open(STATE, "w"))

def write_md(agents, state):
    ok = sum(1 for a in agents if state.get(a.id, {}).get("ok"))
    md = ["# All-Agents Live Test — Real Tasks (paced run)\n",
          f"\n**Summary: {ok}/{len(agents)} agents produced live output.**\n"]
    for i, a in enumerate(agents, 1):
        r = state.get(a.id)
        md.append(f"\n## {i}. {a.name} — {a.title}  ({a.role})\n")
        md.append(f"**Task:** {TASKS.get(a.id, DEFAULT)}\n")
        if r and r.get("ok"):
            md.append(f"**Model:** `{r['model']}` · **Status:** OK\n\n{r['out']}\n")
        else:
            md.append("**Status:** pending (free-tier throttled — will retry)\n")
    open("agent-test-results.md", "w").write("\n".join(md))

async def main():
    agents = get_all_agents()
    state = load_state()
    print(f"Paced run: {len(agents)} agents, {sum(1 for a in agents if state.get(a.id,{}).get('ok'))} already done", flush=True)
    mi = 0
    for rnd in range(MAX_ROUNDS):
        remaining = [a for a in agents if not state.get(a.id, {}).get("ok")]
        if not remaining:
            break
        print(f"-- round {rnd+1}: {len(remaining)} remaining --", flush=True)
        for a in remaining:
            m = MODELS[mi % len(MODELS)]; mi += 1
            settings.moonshot_model = m
            try:
                res = await llm_client._call_moonshot(TASKS.get(a.id, DEFAULT), a.system_prompt, 0.7, 350, None)
                c = content_of(res)
                if c and len(c.strip()) > 30:
                    state[a.id] = {"ok": True, "model": m, "out": c.strip()}
                    save_state(state); write_md(agents, state)
                    print(f"   OK  {a.id:10} via {m} ({len(c)} chars)", flush=True)
            except Exception:
                pass
            await asyncio.sleep(BACKOFF)
    ok = sum(1 for a in agents if state.get(a.id, {}).get("ok"))
    write_md(agents, state)
    print(f"\nDONE: {ok}/{len(agents)} OK -> backend/agent-test-results.md", flush=True)

asyncio.run(main())
