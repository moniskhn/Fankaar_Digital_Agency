"""Run all 23 agents with real role tasks via the agency LLM client (kimi provider)."""
import asyncio
from app.agents.registry import get_all_agents
from app.services.llm_client import llm_client
from run_all_agents import TASKS, DEFAULT

async def main():
    agents = get_all_agents()
    print(f"Running {len(agents)} agents via Kimi (kimi-for-coding)...", flush=True)
    md = ["# All-Agents Live Test — Real Tasks (via Kimi Code, kimi-for-coding)\n"]
    ok = 0
    for i, a in enumerate(agents, 1):
        task = TASKS.get(a.id, DEFAULT)
        text, prov = "", "?"
        for attempt in range(2):
            try:
                res = await llm_client.complete(prompt=task, system=a.system_prompt, max_tokens=400)
                text = (res.text or "").strip(); prov = getattr(res, "provider", "?")
                if prov == "kimi" and len(text) > 20:
                    break
            except Exception as e:
                text = f"[error] {type(e).__name__}: {str(e)[:140]}"
            await asyncio.sleep(2)
        status = "OK" if (prov == "kimi" and len(text) > 20) else f"FAIL({prov})"
        if status == "OK": ok += 1
        print(f"[{i:2}/{len(agents)}] {a.id:10} {a.role:18} -> {status} ({len(text)} chars)", flush=True)
        md.append(f"\n## {i}. {a.name} — {a.title}  ({a.role})\n**Task:** {task}\n**Provider:** {prov} · **Status:** {status}\n\n{text}\n")
        open("agent-test-results.md", "w").write("\n".join(md))
        await asyncio.sleep(0.5)
    md.insert(1, f"\n**Summary: {ok}/{len(agents)} agents produced live Kimi output.**\n")
    open("agent-test-results.md", "w").write("\n".join(md))
    print(f"\nDONE: {ok}/{len(agents)} OK -> backend/agent-test-results.md", flush=True)

asyncio.run(main())
