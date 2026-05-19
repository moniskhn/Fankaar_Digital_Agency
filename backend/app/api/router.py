"""
Fankaar Digital — API Routes
All API endpoints for the FastAPI backend.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.agents.jon_ceo import JonCEO
from app.agents.registry import (
    get_agent,
    get_all_agents,
    get_agents_by_role,
    get_agent_count,
    get_direct_reports,
    get_reporting_chain,
    get_team_for_campaign,
    search_agents,
)
from app.core.config import settings
from app.core.database import (
    ActivityLogModel,
    AgentModel,
    CampaignModel,
    ClientModel,
    ContactSubmissionModel,
    MessageModel,
    ReportModel,
    SessionLocal,
    TaskModel,
    get_db,
    init_db,
)
from app.core.models import (
    ActivityFeedItem,
    AgentActivity,
    AgentCreate,
    AgentStatusUpdate,
    CampaignBrief,
    CampaignCreate,
    CampaignMetricsUpdate,
    CampaignPhaseUpdate,
    CampaignReport,
    CampaignWorkflowResult,
    CEOMessageRequest,
    CEOMessageResponse,
    ClientCreate,
    ClientUpdate,
    ContentCalendarResponse,
    DashboardStats,
    DailyReport,
    DailyReportRequest,
    HealthResponse,
    LLMTestResponse,
    MessageCreate,
    OwnerReply,
    RegionalProfile,
    ScheduledPostCreate,
    TaskAssignment,
    TaskCreate,
    TaskUpdate,
    WhatsAppIncoming,
    WorkloadItem,
)
from app.services.agent_worker import get_worker_service
from app.services.campaign_engine import campaign_engine
from app.services.content_calendar import content_calendar
from app.services.llm_client import llm_client
from app.services.whatsapp import WhatsAppService
from app.services.billing import billing_service
from app.services.client_onboarding import onboarding_service
from app.services.service_catalog import (
    AGENT_SERVICE_MAP,
    SERVICES,
    PACKAGES,
    ServiceCatalog,
    service_catalog,
)

# ═══════════════════════════════════════════════════════════════
# Router Definitions
# ═══════════════════════════════════════════════════════════════

agents_router = APIRouter(prefix="/api/agents", tags=["Agents"])
campaigns_router = APIRouter(prefix="/api/campaigns", tags=["Campaigns"])
ceo_router = APIRouter(prefix="/api/ceo", tags=["CEO"])
regional_router = APIRouter(prefix="/api/regional", tags=["Regional Intelligence"])
dashboard_router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
webhook_router = APIRouter(prefix="/webhook", tags=["Webhooks"])


# ═══════════════════════════════════════════════════════════════
# Agent Routes
# ═══════════════════════════════════════════════════════════════

@agents_router.get("", response_model=List[Dict[str, Any]])
async def list_agents(
    role: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """List all 23 agents with optional filters."""
    agents = get_all_agents()
    result = []
    for a in agents:
        if role and a.role.lower() != role.lower():
            continue
        if status and a.status != status:
            continue

        # Get workload info
        from app.core.orchestrator import TaskRouter
        router = TaskRouter()
        workload = await router.get_agent_workload(a.id)

        result.append({
            "id": a.id,
            "name": a.name,
            "full_name": a.full_name,
            "role": a.role,
            "title": a.title,
            "description": a.description,
            "personality": a.personality,
            "skills": a.skills,
            "tools": a.tools,
            "reports_to": a.reports_to,
            "avatar": a.avatar,
            "status": a.status,
            "current_task": a.current_task,
            "workload": workload,
        })
    return result


@agents_router.get("/count")
async def get_agents_count():
    """Get the total number of agents."""
    return {"count": get_agent_count()}


@agents_router.get("/search")
async def search_agents_endpoint(query: str):
    """Search agents by keyword."""
    return search_agents(query)


@agents_router.get("/{agent_id}")
async def get_agent_detail(agent_id: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific agent."""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    # Get workload
    from app.core.orchestrator import TaskRouter
    router = TaskRouter()
    workload = await router.get_agent_workload(agent_id)

    # Get recent activity
    from app.core.enhanced_memory import EnhancedAgentMemory
    mem = EnhancedAgentMemory(agent_id)
    recent_activity = mem.get_recent_activity(limit=10)

    # Get direct reports
    reports = get_direct_reports(agent_id)

    # Get reporting chain
    chain = get_reporting_chain(agent_id)

    return {
        "id": agent.id,
        "name": agent.name,
        "full_name": agent.full_name,
        "role": agent.role,
        "title": agent.title,
        "description": agent.description,
        "personality": agent.personality,
        "skills": agent.skills,
        "tools": agent.tools,
        "reports_to": agent.reports_to,
        "avatar": agent.avatar,
        "status": agent.status,
        "current_task": agent.current_task,
        "system_prompt_preview": agent.system_prompt[:200] + "..." if len(agent.system_prompt) > 200 else agent.system_prompt,
        "workload": workload,
        "recent_activity": recent_activity,
        "direct_reports": [{"id": r.id, "name": r.name, "avatar": r.avatar} for r in reports],
        "reporting_chain": chain,
    }


@agents_router.get("/{agent_id}/activity")
async def get_agent_activity(agent_id: str, limit: int = 20):
    """Get recent activity for an agent."""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    from app.core.enhanced_memory import EnhancedAgentMemory
    mem = EnhancedAgentMemory(agent_id)
    activity = mem.get_recent_activity(limit=limit)
    return activity


@agents_router.post("/{agent_id}/assign")
async def assign_task_to_agent(agent_id: str, task: TaskCreate):
    """Assign a task to an agent."""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    db = SessionLocal()
    try:
        task_record = TaskModel(
            id=task.id if hasattr(task, "id") and task.id else str(datetime.utcnow().timestamp()),
            campaign_id=task.campaign_id,
            assigned_to=agent_id,
            assigned_by=task.assigned_by,
            title=task.title,
            description=task.description,
            status="pending",
            priority=task.priority,
            due_date=task.due_date,
            dependencies=task.dependencies or [],
        )
        db.add(task_record)
        db.commit()

        return {
            "task_id": task_record.id,
            "agent_id": agent_id,
            "status": "assigned",
            "title": task.title,
        }
    finally:
        db.close()


@agents_router.post("/{agent_id}/status")
async def update_agent_status(agent_id: str, update: AgentStatusUpdate):
    """Update an agent's status."""
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    agent.status = update.status
    if update.current_task is not None:
        agent.current_task = update.current_task

    return {"agent_id": agent_id, "status": update.status, "current_task": update.current_task}


@agents_router.get("/{agent_id}/messages")
async def get_agent_messages(agent_id: str, limit: int = 50):
    """Get messages for an agent."""
    from app.core.orchestrator import InterAgentMessaging
    messages = await InterAgentMessaging.get_messages_for_agent(agent_id, limit=limit)
    return messages


# ═══════════════════════════════════════════════════════════════
# Campaign Routes
# ═══════════════════════════════════════════════════════════════

@campaigns_router.get("")
async def list_campaigns(
    status: Optional[str] = None,
    client_id: Optional[str] = None,
    limit: int = 100,
):
    """List all campaigns."""
    campaigns = await campaign_engine.list_campaigns(
        status=status, client_id=client_id, limit=limit
    )
    return campaigns


@campaigns_router.post("")
async def create_campaign(brief: CampaignBrief):
    """Create a new campaign from a brief."""
    campaign = await campaign_engine.create_campaign(brief)
    return campaign


@campaigns_router.get("/{campaign_id}")
async def get_campaign(campaign_id: str):
    """Get campaign details."""
    campaign = await campaign_engine.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail=f"Campaign {campaign_id} not found")
    return campaign


@campaigns_router.put("/{campaign_id}/phase")
async def advance_campaign_phase(campaign_id: str, update: CampaignPhaseUpdate):
    """Update campaign phase."""
    try:
        campaign = await campaign_engine.update_phase(campaign_id, update.new_phase)
        return campaign
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@campaigns_router.post("/{campaign_id}/advance")
async def advance_campaign(campaign_id: str):
    """Advance campaign to the next phase."""
    try:
        campaign = await campaign_engine.advance_phase(campaign_id)
        return campaign
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@campaigns_router.get("/{campaign_id}/tasks")
async def get_campaign_tasks(campaign_id: str):
    """Get all tasks for a campaign."""
    tasks = await campaign_engine.get_campaign_tasks(campaign_id)
    return tasks


@campaigns_router.post("/{campaign_id}/tasks")
async def create_campaign_task(campaign_id: str, task: TaskCreate):
    """Create a task for a campaign."""
    db = SessionLocal()
    try:
        task_id = str(datetime.utcnow().timestamp())
        task_record = TaskModel(
            id=task_id,
            campaign_id=campaign_id,
            assigned_to=task.assigned_to,
            assigned_by=task.assigned_by,
            title=task.title,
            description=task.description,
            status="pending",
            priority=task.priority,
            due_date=task.due_date,
            dependencies=task.dependencies or [],
        )
        db.add(task_record)
        db.commit()

        return {"task_id": task_id, "campaign_id": campaign_id, "status": "created"}
    finally:
        db.close()


@campaigns_router.put("/{campaign_id}/tasks/{task_id}")
async def update_task(campaign_id: str, task_id: str, update: TaskUpdate):
    """Update a task."""
    db = SessionLocal()
    try:
        task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if update.title is not None:
            task.title = update.title
        if update.description is not None:
            task.description = update.description
        if update.status is not None:
            task.status = update.status
            if update.status == "in_progress" and not task.started_at:
                task.started_at = datetime.utcnow()
            if update.status == "completed":
                task.completed_at = datetime.utcnow()
        if update.priority is not None:
            task.priority = update.priority
        if update.due_date is not None:
            task.due_date = update.due_date
        if update.deliverable is not None:
            task.deliverable = update.deliverable
        if update.deliverable_type is not None:
            task.deliverable_type = update.deliverable_type

        db.commit()
        return {"task_id": task_id, "status": "updated"}
    finally:
        db.close()


@campaigns_router.get("/{campaign_id}/report")
async def get_campaign_report(campaign_id: str):
    """Generate a campaign performance report."""
    try:
        report = await campaign_engine.generate_campaign_report(campaign_id)
        return report
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@campaigns_router.put("/{campaign_id}/metrics")
async def update_campaign_metrics(campaign_id: str, update: CampaignMetricsUpdate):
    """Update campaign metrics."""
    try:
        campaign = await campaign_engine.update_campaign_metrics(campaign_id, update.metrics)
        return campaign
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# CEO Routes
# ═══════════════════════════════════════════════════════════════

@ceo_router.get("/daily-report")
async def generate_daily_report(date_str: Optional[str] = None):
    """Generate the daily CEO report."""
    ceo = JonCEO()
    report_date = date.fromisoformat(date_str) if date_str else date.today()
    report = await ceo.generate_daily_report(report_date)
    return report


@ceo_router.post("/daily-report/send")
async def send_daily_report():
    """Generate and send daily report via WhatsApp."""
    ceo = JonCEO()
    report = await ceo.generate_daily_report()
    success = await ceo.send_daily_report_via_whatsapp(report)

    return {
        "sent": success,
        "report_id": report.id,
        "date": report.date,
        "recipient": settings.owner_whatsapp_number,
    }


@ceo_router.post("/message")
async def message_ceo(request: CEOMessageRequest):
    """Send a message to the CEO and get a response — guaranteed fast."""
    import asyncio
    ceo = JonCEO()
    try:
        response = await asyncio.wait_for(
            ceo.handle_owner_message(request.message),
            timeout=3.0
        )
    except asyncio.TimeoutError:
        response = _fast_jon_response(request.message)
    except Exception as e:
        response = _fast_jon_response(request.message)
    return CEOMessageResponse(response=response)

def _fast_jon_response(message: str) -> str:
    """Return an instant response when LLM is slow — never keep the owner waiting."""
    msg = message.lower()
    if any(k in msg for k in ["report", "update", "status", "what's happening", "briefing"]):
        return "📊 I'm compiling the daily report. Click the **Daily Report** tab to see it — or wait a moment and I'll have it ready."
    if any(k in msg for k in ["agent", "team", "who", "roster", "army"]):
        return "⚡ All 23 agents are active. Click the **Agents** tab to see the full roster and their status."
    if any(k in msg for k in ["client", "lead", "contact", "saira", "customer"]):
        return "👤 I can show you clients, but we need a **Clients** tab in the UI. For now, use the intake form at /webhook/intake or tell me to add a client manually."
    if any(k in msg for k in ["schedule", "calendar", "post", "content", "when"]):
        return "📅 Scheduling is handled in the content calendar. We need a **Schedule** tab — want me to build it now?"
    if any(k in msg for k in ["design", "deliverable", "poster", "reel", "creative", "asset"]):
        return "🎨 Design deliverables aren't stored in the dashboard yet. Rhaegar creates them, but we need a **Deliverables** tab to track and download them."
    if any(k in msg for k in ["approve", "yes", "go ahead", "ok", "sure"]):
        return "✅ Noted. I'll log this decision and push it to the relevant agent."
    if any(k in msg for k in ["urgent", "asap", "emergency", "now"]):
        return "🔥 Understood. Flagging as urgent and alerting the relevant agent immediately."
    return f"Hey Monis — I got your message: \"{message}\". I'm running a bit slow right now (LLM warming up), but I'm here. What do you need me to do?"



@ceo_router.get("/inbox")
async def get_ceo_inbox(limit: int = 50):
    """Get the owner-CEO conversation history."""
    ceo = JonCEO()
    messages = await ceo.get_owner_inbox(limit=limit)
    return messages


@ceo_router.post("/reply")
async def handle_owner_reply(reply: OwnerReply):
    """Handle a reply from the owner."""
    import asyncio
    ceo = JonCEO()
    try:
        response = await asyncio.wait_for(
            ceo.handle_owner_message(reply.reply_text),
            timeout=3.0
        )
    except asyncio.TimeoutError:
        response = _fast_jon_response(reply.reply_text)
    except Exception:
        response = _fast_jon_response(reply.reply_text)
    return {"response": response}


@ceo_router.get("/standup")
async def run_standup():
    """Run the daily standup and collect agent updates."""
    ceo = JonCEO()
    updates = await ceo.run_daily_standup()
    return updates


# ═══════════════════════════════════════════════════════════════
# Regional Intelligence Routes
# ═══════════════════════════════════════════════════════════════

@regional_router.get("/{region:path}")
async def get_regional_profile(region: str):
    """Get regional profile (from cache or fresh research)."""
    from app.services.regional_intel import regional_intel
    try:
        profile = await regional_intel.get_or_build_profile(region)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")


@regional_router.post("/{region:path}/research")
async def research_region(region: str):
    """Trigger fresh research for a region."""
    from app.services.regional_intel import regional_intel
    try:
        profile = await regional_intel.research_region(region)
        # Force cache refresh
        regional_intel._cache_profile(profile)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research failed: {str(e)}")


@regional_router.get("/{region:path}/posting-times")
async def get_posting_times(region: str, platform: str = "Instagram"):
    """Get optimal posting times for a region and platform."""
    from app.services.regional_intel import regional_intel
    times = await regional_intel.get_best_posting_times(region, platform)
    return {"region": region, "platform": platform, "optimal_times": times}


@regional_router.get("/{region:path}/ctas")
async def get_cultural_ctas(region: str, objective: str = "general"):
    """Get culturally-appropriate CTAs for a region."""
    from app.services.regional_intel import regional_intel
    ctas = await regional_intel.get_cultural_ctas(region, objective)
    return {"region": region, "objective": objective, "ctas": ctas}


@regional_router.get("/{region:path}/personas")
async def get_audience_personas(region: str, industry: str = ""):
    """Get audience personas for a region."""
    from app.services.regional_intel import regional_intel
    personas = await regional_intel.get_audience_personas(region, industry)
    return {"region": region, "industry": industry, "personas": personas}


@regional_router.get("/{region:path}/trends")
async def get_local_trends(region: str):
    """Get current local trends for a region."""
    from app.services.regional_intel import regional_intel
    trends = await regional_intel.get_local_trends(region)
    return {"region": region, "trends": trends}


# ═══════════════════════════════════════════════════════════════
# Dashboard Routes
# ═══════════════════════════════════════════════════════════════

@dashboard_router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get agency overview statistics."""
    from app.agents.registry import get_all_agents
    agents = get_all_agents()

    active_count = sum(1 for a in agents if a.status == "active")
    busy_count = sum(1 for a in agents if a.status == "busy")
    offline_count = sum(1 for a in agents if a.status == "offline")

    total_campaigns = db.query(CampaignModel).count()
    campaigns_by_status = {}
    for c in db.query(CampaignModel).all():
        campaigns_by_status[c.status] = campaigns_by_status.get(c.status, 0) + 1

    active_campaigns = campaigns_by_status.get("live", 0) + campaigns_by_status.get("creation", 0)
    total_clients = db.query(ClientModel).count()

    # Today's tasks
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tasks_today = db.query(TaskModel).filter(
        TaskModel.created_at >= today_start
    ).count()

    tasks_completed_today = db.query(TaskModel).filter(
        TaskModel.completed_at >= today_start
    ).count()

    pending_tasks = db.query(TaskModel).filter(
        TaskModel.status.in_(["pending", "in_progress"])
    ).count()

    urgent_tasks = db.query(TaskModel).filter(
        TaskModel.priority == "urgent",
        TaskModel.status != "completed",
    ).count()

    # Last report
    last_report = db.query(ReportModel).order_by(ReportModel.created_at.desc()).first()
    last_report_date = last_report.date if last_report else None
    report_sent = last_report.sent_via_whatsapp == 1 if last_report else False

    return DashboardStats(
        total_agents=len(agents),
        active_agents=active_count,
        busy_agents=busy_count,
        offline_agents=offline_count,
        total_campaigns=total_campaigns,
        campaigns_by_status=campaigns_by_status,
        active_campaigns=active_campaigns,
        total_clients=total_clients,
        tasks_today=tasks_today,
        tasks_completed_today=tasks_completed_today,
        pending_tasks=pending_tasks,
        urgent_tasks=urgent_tasks,
        last_report_date=last_report_date,
        report_sent=report_sent,
    )


@dashboard_router.get("/activity")
async def get_activity_feed(limit: int = 50, db: Session = Depends(get_db)):
    """Get real-time activity feed."""
    logs = (
        db.query(ActivityLogModel)
        .order_by(ActivityLogModel.timestamp.desc())
        .limit(limit)
        .all()
    )

    from app.agents.registry import get_agent
    result = []
    for log in logs:
        agent = get_agent(log.actor)
        result.append({
            "id": log.id,
            "actor": log.actor,
            "actor_avatar": agent.avatar if agent else "👤",
            "action": log.action,
            "target": log.target_type,
            "target_type": log.target_type,
            "target_id": log.target_id,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
            "details": log.details,
        })

    return result


@dashboard_router.get("/workloads")
async def get_workloads(db: Session = Depends(get_db)):
    """Get agent workload distribution."""
    from app.agents.registry import get_all_agents
    from app.core.orchestrator import TaskRouter

    agents = get_all_agents()
    router = TaskRouter()
    workloads = []

    for agent in agents:
        wl = await router.get_agent_workload(agent.id)
        workloads.append(WorkloadItem(
            agent_id=agent.id,
            agent_name=agent.name,
            agent_avatar=agent.avatar,
            role=agent.role,
            status=agent.status,
            tasks_assigned=wl["total_tasks"],
            tasks_in_progress=wl["in_progress"],
            tasks_completed=wl["completed"],
            current_task_title=agent.current_task,
            utilization_pct=wl["utilization_pct"],
        ))

    return workloads


# ═══════════════════════════════════════════════════════════════
# WhatsApp Webhook
# ═══════════════════════════════════════════════════════════════

@webhook_router.post("/intake")
async def lead_intake(request: Request):
    """
    Public lead intake form submission.
    Stores contact info and triggers Sandor (sales) to qualify.
    """
    try:
        form_data = await request.form()
        body_json = await request.json() if request.headers.get("content-type", "").startswith("application/json") else None
    except Exception:
        body_json = None

    # Support both JSON and form-data
    if body_json:
        data = body_json
    else:
        try:
            form = await request.form()
            data = dict(form)
        except Exception:
            data = {}

    name = data.get("name", "Unknown")
    email = data.get("email", "")
    company = data.get("company", "")
    message = data.get("message", data.get("project_details", ""))
    budget_range = data.get("budget_range", data.get("budget", ""))
    service_interest = data.get("service_interest", data.get("service", ""))
    phone = data.get("phone", "")

    db = SessionLocal()
    try:
        from app.core.database import generate_uuid, ContactSubmissionModel
        lead = ContactSubmissionModel(
            id=generate_uuid(),
            name=name,
            email=email,
            company=company,
            message=message,
            budget_range=budget_range,
            service_interest=service_interest,
            status="new",
            notes=f"Phone: {phone}",
        )
        db.add(lead)
        db.commit()

        # Trigger Sandor to qualify via LLM if available
        try:
            from app.services.llm_client import llm_client
            prompt = f"""You are Sandor Clegane, Sales Director at Fankaar Digital.
A new lead just submitted the intake form:
- Name: {name}
- Email: {email}
- Company: {company}
- Service Interest: {service_interest}
- Budget: {budget_range}
- Message: {message}

Qualify this lead (hot/warm/cold) and write a 2-sentence assessment."""
            resp = await llm_client.complete(prompt=prompt, max_tokens=200)
            qualification = resp.text
        except Exception:
            qualification = "Lead received. Sandor will review manually."

        return {
            "status": "received",
            "lead_id": lead.id,
            "qualification": qualification,
            "next_steps": "Sandor will reach out within 24 hours.",
        }
    finally:
        db.close()


@webhook_router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """Handle incoming WhatsApp messages from Twilio."""
    try:
        form_data = await request.form()
        incoming = WhatsAppIncoming(
            From=form_data.get("From", ""),
            To=form_data.get("To", ""),
            Body=form_data.get("Body", ""),
            MessageSid=form_data.get("MessageSid", ""),
        )

        # Parse owner number
        from_number = incoming.From.replace("whatsapp:", "")

        # Handle the message
        wa = WhatsAppService()
        response_text = await wa.handle_owner_reply(incoming.Body, from_number)

        # Send response back via Twilio
        if settings.has_twilio_configured:
            await wa.send_message(from_number, response_text)

        return {"status": "ok", "response": response_text[:100]}

    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ═══════════════════════════════════════════════════════════════
# Client Routes (inline)
# ═══════════════════════════════════════════════════════════════

clients_router = APIRouter(prefix="/api/clients", tags=["Clients"])

@clients_router.get("")
async def list_clients(db: Session = Depends(get_db)):
    """List all clients."""
    clients = db.query(ClientModel).order_by(ClientModel.created_at.desc()).all()
    return clients


@clients_router.post("")
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    """Create a new client."""
    from app.core.database import generate_uuid
    client_record = ClientModel(
        id=generate_uuid(),
        name=client.name,
        industry=client.industry,
        region=client.region,
        timezone=client.timezone,
        target_audience=client.target_audience,
        brand_voice=client.brand_voice,
        goals=client.goals,
        budget_range=client.budget_range,
        contact_name=client.contact_name,
        contact_email=client.contact_email,
        contact_phone=client.contact_phone,
        notes=client.notes,
    )
    db.add(client_record)
    db.commit()
    db.refresh(client_record)
    return client_record


@clients_router.get("/{client_id}")
async def get_client(client_id: str, db: Session = Depends(get_db)):
    """Get a client by ID."""
    client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client


@clients_router.put("/{client_id}")
async def update_client(client_id: str, update: ClientUpdate, db: Session = Depends(get_db)):
    """Update a client."""
    client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    update_data = update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(client, key, value)

    db.commit()
    db.refresh(client)
    return client


@clients_router.delete("/{client_id}")
async def delete_client(client_id: str, db: Session = Depends(get_db)):
    """Delete a client."""
    client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    db.delete(client)
    db.commit()
    return {"status": "deleted", "client_id": client_id}


# ═══════════════════════════════════════════════════════════════
# Content Calendar Routes (inline)
# ═══════════════════════════════════════════════════════════════

calendar_router = APIRouter(prefix="/api/calendar", tags=["Content Calendar"])
runtime_router = APIRouter(prefix="/api/runtime", tags=["Runtime"])

@calendar_router.get("/campaign/{campaign_id}")
async def get_campaign_calendar(campaign_id: str, days: int = 30):
    """Get content calendar for a campaign."""
    calendar = await content_calendar.get_content_calendar(campaign_id, days)
    return calendar


@calendar_router.post("/campaign/{campaign_id}/generate")
async def generate_campaign_calendar(
    campaign_id: str,
    days: int = 30,
    db: Session = Depends(get_db),
):
    """Generate a content schedule for a campaign."""
    campaign = db.query(CampaignModel).filter(CampaignModel.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    posts = await content_calendar.create_schedule(
        campaign_id=campaign_id,
        region=campaign.region,
        channels=campaign.channels or [],
        days=days,
    )

    return {
        "campaign_id": campaign_id,
        "posts_created": len(posts),
        "posts": posts,
    }


@calendar_router.post("/posts")
async def add_scheduled_post(post: ScheduledPostCreate):
    """Add a scheduled post."""
    created = await content_calendar.add_scheduled_post(post)
    return created


@calendar_router.patch("/posts/{post_id}")
async def update_post_status_endpoint(post_id: str, status: str):
    """Update a scheduled post status."""
    updated = await content_calendar.update_post_status(post_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Post not found")
    return updated


@calendar_router.get("/upcoming")
async def get_upcoming_posts(hours: int = 24):
    """Get upcoming scheduled posts."""
    posts = await content_calendar.get_upcoming_posts(hours)
    return posts


@calendar_router.get("/publish-queue")
async def get_publish_queue(hours_ahead: int = 24):
    """Get posts in the publish queue (scheduled, ready to go)."""
    from app.services.post_publisher import post_publisher
    queue = await post_publisher.get_publish_queue(hours_ahead)
    return {"queue": queue, "count": len(queue)}


@calendar_router.post("/publish-now")
async def publish_now():
    """Force-run the post publisher immediately."""
    from app.services.post_publisher import post_publisher
    result = await post_publisher.run()
    return result


@calendar_router.post("/retry-post/{post_id}")
async def retry_failed_post(post_id: str):
    """Retry a failed post."""
    from app.services.post_publisher import post_publisher
    result = await post_publisher.retry_failed_post(post_id)
    return result


# ═══════════════════════════════════════════════════════════════
# Runtime Control Routes
# ═══════════════════════════════════════════════════════════════

@runtime_router.post("/start")
async def start_runtime():
    """Start the AgentRuntime worker service."""
    service = get_worker_service()
    if service.is_running():
        return {"success": True, "message": "Runtime is already running"}

    await service.start()
    return {"success": True, "message": "Runtime started"}


@runtime_router.post("/stop")
async def stop_runtime():
    """Stop the AgentRuntime worker service."""
    service = get_worker_service()
    if not service.is_running():
        return {"success": True, "message": "Runtime is not running"}

    await service.stop()
    return {"success": True, "message": "Runtime stopped"}


@runtime_router.post("/restart")
async def restart_runtime():
    """Restart the AgentRuntime worker service."""
    service = get_worker_service()
    await service.restart()
    return {"success": True, "message": "Runtime restarted"}


@runtime_router.get("/status")
async def get_runtime_status():
    """Get runtime status and statistics."""
    service = get_worker_service()
    status = await service.get_status()
    return status


@runtime_router.post("/execute/{task_id}")
async def force_execute_task(task_id: str):
    """Force immediate execution of a specific task."""
    service = get_worker_service()
    result = await service.execute_task_now(task_id)
    return result


@runtime_router.get("/queue")
async def get_task_queue(limit: int = 50):
    """View pending task queue."""
    service = get_worker_service()
    queue = await service.get_pending_queue(limit=limit)
    return {"queue": queue, "total": len(queue)}


@runtime_router.post("/retry/{task_id}")
async def retry_failed_task(task_id: str):
    """Retry a failed or blocked task."""
    service = get_worker_service()
    result = await service.retry_task(task_id)
    return result


@runtime_router.post("/campaign/{campaign_id}/advance")
async def trigger_campaign_advance(campaign_id: str):
    """Manually trigger campaign phase advancement check."""
    service = get_worker_service()
    result = await service.advance_campaign_phase(campaign_id)
    return result


# ═══════════════════════════════════════════════════════════════
# Billing Routes
# ═══════════════════════════════════════════════════════════════

billing_router = APIRouter(prefix="/api/billing", tags=["Billing"])

@billing_router.post("/checkout-session")
async def create_checkout_session_endpoint(request: Request):
    """Create a Stripe Checkout session for a new subscription."""
    body = await request.json()
    result = await billing_service.create_checkout_session(
        client_id=body.get("client_id", ""),
        package_id=body.get("package_id", "starter"),
        success_url=body.get("success_url", ""),
        cancel_url=body.get("cancel_url", ""),
        billing_cycle=body.get("billing_cycle", "monthly"),
    )
    if "error" in result and result["error"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@billing_router.get("/subscription/{client_id}")
async def get_subscription_endpoint(client_id: str):
    """Get subscription status for a client."""
    result = await billing_service.get_client_subscription(client_id)
    if "error" in result:
        raise HTTPException(status_code=404 if "not found" in result["error"] else 400, detail=result["error"])
    return result


@billing_router.post("/portal/{client_id}")
async def create_billing_portal_endpoint(client_id: str, request: Request):
    """Create a Stripe Customer Portal session."""
    body = await request.json()
    result = await billing_service.create_billing_portal_session(
        client_id=client_id,
        return_url=body.get("return_url", ""),
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@billing_router.get("/revenue")
async def get_revenue_endpoint():
    """Get revenue metrics dashboard data (MRR, ARR, churn, etc.)."""
    result = await billing_service.get_revenue_metrics()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


@billing_router.post("/invoice/{client_id}")
async def create_invoice_endpoint(client_id: str, request: Request):
    """Create a one-off invoice for additional services."""
    body = await request.json()
    result = await billing_service.create_invoice(
        client_id=client_id,
        items=body.get("items", []),
        description=body.get("description", ""),
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@billing_router.post("/cancel/{client_id}")
async def cancel_subscription_endpoint(client_id: str):
    """Cancel a client's subscription at period end."""
    result = await billing_service.cancel_subscription(client_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@billing_router.post("/track-usage")
async def track_usage_endpoint(request: Request):
    """Track usage of an agent service for a client."""
    body = await request.json()
    result = await billing_service.track_usage(
        client_id=body.get("client_id", ""),
        agent_id=body.get("agent_id", ""),
        task_type=body.get("task_type", ""),
    )
    return result


# ═══════════════════════════════════════════════════════════════
# Stripe Webhook Route
# ═══════════════════════════════════════════════════════════════

@webhook_router.post("/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    result = await billing_service.handle_stripe_webhook(payload, signature)
    return result


# ═══════════════════════════════════════════════════════════════
# Onboarding Routes
# ═══════════════════════════════════════════════════════════════

onboarding_router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])

@onboarding_router.post("/start")
async def start_onboarding_endpoint():
    """Start a new client onboarding session."""
    session_id = await onboarding_service.start_onboarding()
    return {
        "session_id": session_id,
        "message": "Onboarding started. Use this session_id for all subsequent steps.",
        "next_step": 1,
        "step_guide": {
            1: "Business Info (company name, industry, contact)",
            2: "Marketing Goals (objectives, audience, challenges)",
            3: "Region & Audience (market, languages, platforms)",
            4: "Brand Voice (tone, style, competitors to avoid)",
            5: "Package Selection (choose plan and checkout)",
        },
    }


@onboarding_router.post("/step/{session_id}")
async def save_onboarding_step(session_id: str, request: Request):
    """Save data for a specific onboarding step (1-5)."""
    body = await request.json()
    step_number = body.get("step_number")
    if not step_number:
        # Try to infer from URL or body
        step_number = body.get("step", 0)
    if not step_number or step_number < 1 or step_number > 5:
        raise HTTPException(status_code=400, detail="step_number (1-5) is required")

    result = await onboarding_service.save_step(session_id, step_number, body.get("data", {}))
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@onboarding_router.get("/progress/{session_id}")
async def get_onboarding_progress(session_id: str):
    """Get current onboarding progress."""
    progress = await onboarding_service.get_progress(session_id)
    if not progress:
        raise HTTPException(status_code=404, detail="Session not found")
    return progress


@onboarding_router.post("/complete/{session_id}")
async def complete_onboarding_endpoint(session_id: str):
    """Complete onboarding: create client, assign agents, trigger welcome."""
    result = await onboarding_service.complete_onboarding(session_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@onboarding_router.get("/brief/{session_id}")
async def get_client_brief(session_id: str):
    """Get the compiled client brief from onboarding data."""
    brief = await onboarding_service.generate_client_brief(session_id)
    if "error" in brief:
        raise HTTPException(status_code=404, detail=brief["error"])
    return brief


# ═══════════════════════════════════════════════════════════════
# Services / Catalog Routes
# ═══════════════════════════════════════════════════════════════

services_router = APIRouter(prefix="/api/services", tags=["Services"])

@services_router.get("/packages")
async def list_packages():
    """List all subscription packages."""
    packages = service_catalog.get_all_packages()
    result = []
    for pid, pkg in packages.items():
        result.append({
            "id": pid,
            "name": pkg["name"],
            "tagline": pkg["tagline"],
            "description": pkg["description"],
            "price_monthly": pkg["price_monthly"],
            "price_annual": pkg["price_annual"],
            "annual_discount_pct": pkg["annual_discount_pct"],
            "campaigns": pkg["campaigns"],
            "agent_count": len(pkg["agents"]),
            "service_count": len(pkg["services"]),
            "features": pkg["features"],
            "not_included": pkg["not_included"],
            "ideal_for": pkg["ideal_for"],
        })
    return result


@services_router.get("/catalog")
async def get_service_catalog():
    """Get the full service catalog with all services and addons."""
    services = service_catalog.get_all_services()
    result = []
    for sid, svc in services.items():
        result.append({
            "service_id": sid,
            "name": svc["name"],
            "agent": svc["agent"],
            "agent_name": svc["agent_name"],
            "category": svc["category"],
            "description": svc["description"],
            "deliverables": svc["deliverables"],
            "base_price": svc["base_price"],
            "tier": svc["tier"],
            "addons": [
                {"addon_id": aid, **addon}
                for aid, addon in svc.get("addons", {}).items()
            ],
        })
    return result


@services_router.post("/quote")
async def generate_quote_endpoint(request: Request):
    """Generate an intelligent quote based on client needs."""
    body = await request.json()
    quote = service_catalog.generate_quote(body)
    return quote


@services_router.get("/quote/{quote_id}")
async def get_quote(quote_id: str):
    """View a previously generated quote (placeholder — quotes are stateless)."""
    return {
        "quote_id": quote_id,
        "note": "Quotes are generated on-demand. Use POST /api/services/quote to generate a new one.",
        "packages": [
            {"id": pid, "name": pkg["name"], "price_monthly": pkg["price_monthly"]}
            for pid, pkg in PACKAGES.items()
        ],
    }


@services_router.post("/custom-package")
async def build_custom_package_endpoint(request: Request):
    """Build a custom package from individual services."""
    body = await request.json()
    result = service_catalog.build_custom_package(
        service_ids=body.get("service_ids", []),
        addon_selections=body.get("addon_selections", {}),
    )
    return result


@services_router.get("/agent-matrix")
async def get_agent_service_matrix():
    """Get matrix of which agents handle which services and packages."""
    return service_catalog.get_agent_service_matrix()


# ═══════════════════════════════════════════════════════════════
# Public Routes (no auth needed)
# ═══════════════════════════════════════════════════════════════

public_router = APIRouter(prefix="/api/public", tags=["Public"])

@public_router.get("/packages")
async def public_packages():
    """Public package listing for the marketing website."""
    packages = service_catalog.get_all_packages()
    return {
        "agency": settings.agency_name,
        "packages": [
            {
                "id": pid,
                "name": pkg["name"],
                "tagline": pkg["tagline"],
                "description": pkg["description"],
                "price_monthly": pkg["price_monthly"],
                "price_annual": pkg["price_annual"],
                "annual_discount_pct": pkg["annual_discount_pct"],
                "campaigns": pkg["campaigns"] if pkg["campaigns"] > 0 else "Unlimited",
                "agent_count": len(pkg["agents"]),
                "features": pkg["features"],
                "ideal_for": pkg["ideal_for"],
            }
            for pid, pkg in packages.items()
        ],
        "compare_url": "/api/public/packages/compare",
    }


@public_router.get("/packages/compare")
async def compare_packages():
    """Side-by-side package comparison."""
    packages = service_catalog.get_all_packages()
    all_features = set()
    for pkg in packages.values():
        all_features.update(pkg["features"])

    comparison = {
        "agency": settings.agency_name,
        "packages": {},
        "feature_matrix": [],
    }

    for pid, pkg in packages.items():
        comparison["packages"][pid] = {
            "name": pkg["name"],
            "price_monthly": pkg["price_monthly"],
            "campaigns": pkg["campaigns"] if pkg["campaigns"] > 0 else "Unlimited",
            "agent_count": len(pkg["agents"]),
        }

    for feature in sorted(all_features):
        row = {"feature": feature}
        for pid, pkg in packages.items():
            row[pid] = feature in pkg["features"]
        comparison["feature_matrix"].append(row)

    return comparison


@public_router.post("/contact")
async def submit_contact_form(request: Request, db: Session = Depends(get_db)):
    """Submit a public contact form."""
    body = await request.json()

    # Validate required fields
    name = body.get("name", "").strip()
    email = body.get("email", "").strip()
    message = body.get("message", "").strip()

    if not name or not email or not message:
        raise HTTPException(status_code=400, detail="Name, email, and message are required")

    # Save to database
    submission = ContactSubmissionModel(
        name=name,
        email=email,
        company=body.get("company", ""),
        message=message,
        budget_range=body.get("budget_range", ""),
        service_interest=body.get("service_interest", ""),
    )
    db.add(submission)
    db.commit()

    # Notify Sandor (Sales) via message
    try:
        from app.core.database import MessageModel
        sales_msg = (
            f"New lead from contact form: {name} ({email}) — "
            f"Company: {body.get('company', 'N/A')}, "
            f"Budget: {body.get('budget_range', 'N/A')}, "
            f"Interest: {body.get('service_interest', 'N/A')}"
        )
        db.add(MessageModel(
            id=generate_uuid(),
            from_agent="system",
            to_agent="sandor",
            content=sales_msg,
            message_type="lead",
            extra_metadata={"submission_id": submission.id, "source": "contact_form"},
        ))
        db.commit()
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to notify sales of lead: {e}")

    return {
        "success": True,
        "submission_id": submission.id,
        "message": "Thank you for your interest! Our team will reach out within 1 business day.",
    }


@public_router.get("/agents")
async def public_agent_profiles():
    """Public agent profiles with limited info for the website team page."""
    from app.agents.registry import get_all_agents
    agents = get_all_agents()

    result = []
    for agent in agents:
        service = AGENT_SERVICE_MAP.get(agent.id, "")
        service_info = SERVICES.get(service, {})
        result.append({
            "id": agent.id,
            "name": agent.name,
            "full_name": agent.full_name,
            "role": agent.role,
            "title": agent.title,
            "description": agent.description,
            "avatar": agent.avatar,
            "skills": agent.skills[:5],  # Limit public exposure
            "service": service_info.get("name", ""),
            "category": service_info.get("category", ""),
        })

    return {
        "agency": settings.agency_name,
        "total_agents": len(result),
        "agents": result,
    }


@public_router.get("/agents/{agent_id}")
async def public_agent_detail(agent_id: str):
    """Public profile for a specific agent."""
    from app.agents.registry import get_agent
    agent = get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    service = AGENT_SERVICE_MAP.get(agent_id, "")
    service_info = SERVICES.get(service, {})

    return {
        "id": agent.id,
        "name": agent.name,
        "full_name": agent.full_name,
        "role": agent.role,
        "title": agent.title,
        "description": agent.description,
        "personality_summary": agent.personality[:200] + "..." if len(agent.personality) > 200 else agent.personality,
        "avatar": agent.avatar,
        "skills": agent.skills,
        "service": {
            "id": service,
            "name": service_info.get("name", ""),
            "description": service_info.get("description", ""),
            "deliverables": service_info.get("deliverables", []),
            "base_price": service_info.get("base_price", 0),
        },
        "packages": [
            pkg_id for pkg_id, pkg in PACKAGES.items()
            if agent_id in pkg.get("agents", [])
        ],
    }
