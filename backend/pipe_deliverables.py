"""Pipe generated agent deliverables (Saira + 23-agent run) into the live DB as
completed campaign tasks so they appear in the dashboard Deliverables tab."""
import re, uuid
from datetime import datetime
from app.core.database import SessionLocal, CampaignModel, ClientModel, TaskModel, AgentModel, init_db
from app.agents.registry import get_all_agents

init_db()
db = SessionLocal()
name2id = {a.name.lower(): a.id for a in get_all_agents()}
valid_ids = {a.id for a in db.query(AgentModel).all()} or set(name2id.values())

def parse_sections(path):
    try:
        txt = open(path).read()
    except FileNotFoundError:
        return []
    out = []
    for chunk in re.split(r'\n##\s+', txt)[1:]:
        lines = chunk.splitlines()
        header = lines[0].strip()
        m = re.match(r'(?:\d+\.\s*)?(.+?)\s+—\s+(.+?)(?:\s+\(([^)]+)\))?$', header)
        if not m:
            continue
        name, title = m.group(1).strip(), m.group(2).strip()
        task = ""
        body_start = 1
        for i, l in enumerate(lines[1:], 1):
            if l.startswith("**Task:**"):
                task = l.replace("**Task:**", "").strip()
            if l.startswith("**Provider:**") or l.startswith("**Model:**"):
                body_start = i + 1
        body = "\n".join(lines[body_start:]).strip()
        out.append({"name": name, "title": title, "task": task, "body": body})
    return out

def ensure_client(name, industry, region):
    c = db.query(ClientModel).filter(ClientModel.name == name).first()
    if not c:
        c = ClientModel(id=str(uuid.uuid4()), name=name, industry=industry, region=region, status="active")
        db.add(c); db.commit()
    return c

def make_campaign(client_id, name, region):
    c = db.query(CampaignModel).filter(CampaignModel.name == name).first()
    if not c:
        c = CampaignModel(id=str(uuid.uuid4()), client_id=client_id, name=name, status="live", region=region)
        db.add(c); db.commit()
    return c

def add_tasks(campaign, sections, default_region):
    n = 0
    for s in sections:
        if not s["body"] or len(s["body"]) < 20:
            continue
        aid = name2id.get(s["name"].lower())
        if aid not in valid_ids:
            aid = "jon" if "jon" in valid_ids else next(iter(valid_ids))
        title = (s["task"][:70] + "…") if s["task"] else f"{s['name']} deliverable"
        t = TaskModel(
            id=str(uuid.uuid4()), campaign_id=campaign.id, assigned_to=aid, assigned_by="jon",
            title=f"{s['name']}: {title}", description=s["task"] or s["title"],
            status="completed", deliverable=s["body"], deliverable_type="document",
            started_at=datetime.utcnow(), completed_at=datetime.utcnow(),
        )
        db.add(t); n += 1
    db.commit(); return n

# 1) Saira deliverables
saira = ensure_client("Saira Contracting", "Interior Fit-Out", "Dubai")
camp1 = make_campaign(saira.id, "Saira Contracting — Social & Web", "Dubai")
n1 = add_tasks(camp1, parse_sections("saira-agent-output.md"), "Dubai")

# 2) 23-agent capability run
demo = ensure_client("Fankaar Internal", "Agency", "Dubai")
camp2 = make_campaign(demo.id, "Agency Capability Demo (23 agents)", "Dubai")
n2 = add_tasks(camp2, parse_sections("agent-test-results.md"), "Dubai")

print(f"Saira deliverables piped: {n1}  |  23-agent deliverables piped: {n2}")
print(f"Campaigns: '{camp1.name}', '{camp2.name}'")
db.close()
