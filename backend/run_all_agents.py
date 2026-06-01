"""Run every agent with a real, role-appropriate task via the agency's own LLM client.
Cycles free OpenRouter models on 429. Writes full results to agent-test-results.md."""
import asyncio, time
from app.agents.registry import get_all_agents
from app.services.llm_client import llm_client

MODELS = [
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "meta-llama/llama-3.2-3b-instruct:free",
    "qwen/qwen3-coder:free",
    "z-ai/glm-4.5-air:free",
    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
    "nousresearch/hermes-3-llama-3.1-405b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]

# Real, role-aware tasks. Context: agency 'Fankaar/Claude Mythos', clients
# Winterfell Co. (tourism, The North) and Casterly Rock (finance, Westerlands).
TASKS = {
 "jon":"As CEO, give your top 3 priorities this week to grow revenue across our two clients. Brief, specific.",
 "sandor":"Qualify this inbound lead in 3 crisp bullets: a 12-room boutique lodge wants winter bookings, budget unclear.",
 "sansa":"Draft a 2-sentence PR holding statement for a client after a delayed-refund complaint went viral.",
 "rhaegar":"Describe a hero visual concept (1 paragraph) for Winterfell Co.'s Winter Sale — mood, composition, palette.",
 "gendry":"List the 4 components and 1 API call needed to build a 'Book Now' widget for the Winterfell landing page.",
 "tywin":"Given $36k combined monthly client spend at 22% margin, state our gross profit and one cost risk. Brief.",
 "olenna":"Write a 2-line internal note welcoming a new junior designer and setting week-1 expectations.",
 "stannis":"Flag the top 2 legal risks in running a 'limited-time 25% off' tourism promo. One line each.",
 "brienne":"Lay out a 4-step operations plan to launch the Winterfell Winter Sale campaign on time.",
 "podrick":"Write a warm 2-sentence reply to a guest asking if the winter rate includes breakfast.",
 "arya":"Give 3 competitor insights to watch for a boutique winter-tourism brand in The North.",
 "bran":"State a one-paragraph positioning strategy for Casterly Rock (finance) vs bigger banks.",
 "cersei":"Draft a firm 2-line negotiation stance to a vendor who raised ad-management fees 15%.",
 "davos":"Write a 3-sentence client check-in email updating Winterfell Co. on Winter Sale progress.",
 "jorah":"Suggest 3 retention moves to keep Casterly Rock past their first contract term.",
 "tyrion":"Write 3 Instagram captions for Winterfell Co.'s Winter Sale: hook + emoji + CTA. Number them.",
 "sandoq":"Give 5 SEO keywords + 1 meta title for a 'winter cabin getaway in the North' landing page.",
 "missandei":"Plan a 1-week IG posting schedule (days + format) for the Winter Sale. Bullets.",
 "bronn":"Recommend a starter Meta ads structure (campaign/adset/budget split) for a $4k/mo winter promo.",
 "samwell":"List the 5 KPIs to track for a tourism booking campaign and why each matters. Brief.",
 "margaery":"Outline a 3-email winter-sale sequence (subject + 1-line goal each).",
 "petyr":"Summarize what a weekly client report for Winterfell Co. should contain — 5 sections.",
 "greyworm":"Suggest 3 conversion-rate optimizations for a hotel 'Book Now' funnel. One line each.",
}
DEFAULT = "In 3 concise bullets, do your core job for our client Winterfell Co.'s Winter Sale campaign."

def content_of(res):
    for a in ("content","text","message","output","response"):
        v = getattr(res, a, None)
        if isinstance(v, str) and v.strip():
            return v
    return None

async def run_one(agent):
    task = TASKS.get(agent.id, DEFAULT)
    for attempt in range(2):            # two full passes over the model pool
        for m in MODELS:
            from app.core.config import settings
            settings.moonshot_model = m
            try:
                res = await llm_client._call_moonshot(task, agent.system_prompt, 0.7, 350, None)
                c = content_of(res)
                if c and len(c.strip()) > 30:
                    return {"ok": True, "model": m, "task": task, "out": c.strip()}
            except Exception as e:
                s = str(e)
                code = "429" if "429" in s else ("404" if "404" in s else type(e).__name__)
                if code != "429" and code != "404":
                    return {"ok": False, "model": m, "task": task, "out": f"[{code}] {s[:160]}"}
            await asyncio.sleep(2)
        await asyncio.sleep(5)
    return {"ok": False, "model": "-", "task": task, "out": "[throttled] all free models 429/empty after 2 passes"}

async def main():
    agents = get_all_agents()
    print(f"Running {len(agents)} agents...", flush=True)
    md = ["# All-Agents Live Test — Real Tasks\n",
          "Each agent ran a role-specific real task through the agency LLM client (OpenRouter free models).\n"]
    ok = 0
    for i, a in enumerate(agents, 1):
        r = await run_one(a)
        status = "OK" if r["ok"] else "THROTTLED/ERR"
        if r["ok"]: ok += 1
        print(f"[{i:2}/{len(agents)}] {a.id:10} {a.role:16} -> {status} ({r['model']}, {len(r['out'])} chars)", flush=True)
        md.append(f"\n## {i}. {a.name} — {a.title}  ({a.role})\n")
        md.append(f"**Task:** {r['task']}\n")
        md.append(f"**Model:** `{r['model']}` · **Status:** {status}\n\n")
        md.append((r["out"] if r["ok"] else f"> {r['out']}") + "\n")
        # write incrementally so partial results survive
        open("agent-test-results.md","w").write("\n".join(md))
        await asyncio.sleep(1)
    md.insert(2, f"\n**Summary: {ok}/{len(agents)} agents produced live output.**\n")
    open("agent-test-results.md","w").write("\n".join(md))
    print(f"\nDONE: {ok}/{len(agents)} OK. Full results -> backend/agent-test-results.md", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
