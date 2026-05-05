"""
Claude Mythos — FastAPI Entry Point
Main application with CORS, routers, startup/shutdown events, health check.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.api.router import (
    agents_router,
    billing_router,
    campaigns_router,
    ceo_router,
    clients_router,
    onboarding_router,
    public_router,
    regional_router,
    dashboard_router,
    services_router,
    webhook_router,
    calendar_router,
    runtime_router,
)
from app.services.agent_worker import get_worker_service

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    # ── Startup ──────────────────────────────────────────────────
    logger.info(f"🚀 Starting {settings.agency_name} backend...")
    logger.info(f"   Environment: {settings.app_env}")
    logger.info(f"   LLM Provider: {settings.llm_provider}")
    logger.info(f"   Database: {settings.database_path}")

    # Initialize database tables
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
    logger.error(f"❌ Database initialization failed: {e}")
    logger.info("🔄 Continuing without database...")

    # Seed agent definitions into database
    try:
        from app.core.database import AgentModel, SessionLocal
        from app.agents.registry import get_all_agents

        db = SessionLocal()
        try:
            existing_count = db.query(AgentModel).count()
            if existing_count == 0:
                logger.info("🌱 Seeding agent definitions...")
                agents = get_all_agents()
                for agent in agents:
                    db_agent = AgentModel(
                        id=agent.id,
                        name=agent.name,
                        full_name=agent.full_name,
                        role=agent.role,
                        title=agent.title,
                        description=agent.description,
                        personality=agent.personality,
                        skills=agent.skills,
                        tools=agent.tools,
                        reports_to=agent.reports_to,
                        avatar=agent.avatar,
                        status=agent.status,
                        system_prompt=agent.system_prompt,
                    )
                    db.add(db_agent)
                db.commit()
                logger.info(f"✅ Seeded {len(agents)} agents")
            else:
                logger.info(f"📊 {existing_count} agents already in database")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"⚠️ Agent seeding warning: {e}")

    # Test LLM connection
    try:
        from app.services.llm_client import llm_client
        health = await llm_client.check_health()
        if health["available"]:
            logger.info(f"✅ LLM connected: {health['provider']}/{health['model']} ({health['latency_ms']:.0f}ms)")
        else:
            logger.warning(f"⚠️ LLM not available: {health.get('error', 'unknown')}")
    except Exception as e:
        logger.warning(f"⚠️ LLM health check failed: {e}")

    # Check WhatsApp configuration
    if settings.has_twilio_configured:
        logger.info("✅ WhatsApp (Twilio) configured")
    else:
        logger.info("ℹ️ WhatsApp not configured — messages will be logged only")

    # Check Stripe configuration
    if settings.has_stripe_configured:
        logger.info("✅ Stripe billing configured")
    else:
        logger.info("ℹ️ Stripe not configured — billing features will use mock mode")

    # Start the AgentRuntime worker service
    try:
        worker = get_worker_service()
        await worker.start()
        logger.info("🤖 AgentRuntime worker service started")
    except Exception as e:
        logger.error(f"❌ Failed to start AgentRuntime: {e}")
        # Don't raise -- the API should still work even if runtime fails

    logger.info(f"🏰 {settings.agency_name} is ready")
    yield

    # ── Shutdown ─────────────────────────────────────────────────
    logger.info(f"👋 {settings.agency_name} shutting down...")

    # Stop the worker service
    try:
        worker = get_worker_service()
        await worker.stop()
        logger.info("🤖 AgentRuntime worker service stopped")
    except Exception as e:
        logger.warning(f"Error stopping AgentRuntime: {e}")


# ── Create FastAPI App ─────────────────────────────────────────

app = FastAPI(
    title=settings.agency_name,
    description="AI Digital Marketing Agency — 23 AI employees, AI CEO, daily WhatsApp reports",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include Routers ────────────────────────────────────────────

app.include_router(agents_router)
app.include_router(campaigns_router)
app.include_router(ceo_router)
app.include_router(clients_router)
app.include_router(regional_router)
app.include_router(dashboard_router)
app.include_router(webhook_router)
app.include_router(calendar_router)
app.include_router(runtime_router)
app.include_router(billing_router)
app.include_router(onboarding_router)
app.include_router(services_router)
app.include_router(public_router)


# ── Health Check ───────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from app.agents.registry import get_agent_count
    from app.services.llm_client import llm_client
    from app.services.whatsapp import WhatsAppService

    llm_health = await llm_client.check_health()
    wa = WhatsAppService()

    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() if 'datetime' in dir() else "now",
        "llm_provider": settings.llm_provider,
        "llm_available": llm_health.get("available", False),
        "whatsapp_configured": settings.has_twilio_configured,
        "stripe_configured": settings.has_stripe_configured,
        "database_connected": True,
        "agent_count": get_agent_count(),
        "environment": settings.app_env,
    }


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API info."""
    return {
        "name": settings.agency_name,
        "version": "1.0.0",
        "description": "AI Digital Marketing Agency with 23 AI employees",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "agents": "/api/agents",
            "campaigns": "/api/campaigns",
            "ceo": "/api/ceo",
            "clients": "/api/clients",
            "regional": "/api/regional/{region}",
            "dashboard": "/api/dashboard/stats",
            "webhook": "/webhook/whatsapp",
            "billing": "/api/billing",
            "onboarding": "/api/onboarding",
            "services": "/api/services",
            "public": "/api/public",
        },
    }


# ── Import datetime for health check ───────────────────────────
from datetime import datetime
