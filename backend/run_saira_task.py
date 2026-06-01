"""Run real Saira Contracting tasks through agency agents via Kimi."""
import asyncio
from app.agents.registry import get_agent
from app.services.llm_client import llm_client

JOBS = [
    ("tyrion", "Write 3 Instagram captions for Saira Contracting — a Dubai luxury interior fit-out & bespoke joinery firm — showcasing their completed Black Tap restaurant fit-out at Dubai Mall. Each: a hook, 1-2 lines, one emoji, a booking CTA, and 3 hashtags. Number them 1-3."),
    ("bronn", "Write a Meta click-to-WhatsApp lead ad for Saira Contracting targeting Dubai restaurant, retail and office owners planning a fit-out. Give: Primary text, Headline (<=40 chars), Description, and CTA button. Emphasise a free 3D concept + realistic timeline, and that DM/Civil Defense approvals are handled. WhatsApp +971 4 399 0489."),
    ("sandoq", "Give Saira Contracting (interior fit-out & joinery, Dubai) 8 high-intent local SEO keywords (restaurant/retail/office fit-out focus) and 3 meta-title options (<=60 chars each). Brief table or list."),
]

async def main():
    out = ["# Saira Contracting — Live Agent Deliverables (via Kimi)\n"]
    for aid, task in JOBS:
        a = get_agent(aid)
        print(f"-- {a.name} ({a.role}) ...", flush=True)
        try:
            res = await llm_client.complete(prompt=task, system=a.system_prompt, max_tokens=600)
            text = (res.text or "").strip(); prov = getattr(res, "provider", "?")
        except Exception as e:
            text, prov = f"[error] {e}", "err"
        print(f"   {prov} · {len(text)} chars", flush=True)
        out.append(f"\n## {a.name} — {a.title}\n**Task:** {task}\n**Provider:** {prov}\n\n{text}\n")
        open("saira-agent-output.md", "w").write("\n".join(out))
    print("DONE -> backend/saira-agent-output.md", flush=True)

asyncio.run(main())
