"""
Claude Mythos — FastAPI Entry Point
"""
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _load_routers():
    """Load all API routers with error handling."""
    routers = []
    router_specs = [
        ("app.api.router", "agents_router", "/api/agents"),
        ("app.api.router", "campaigns_router", "/api/campaigns"),
        ("app.api.router", "ceo_router", "/api/ceo"),
        ("app.api.router", "clients_router", "/api/clients"),
        ("app.api.router", "regional_router", "/api/regional"),
        ("app.api.router", "dashboard_router", "/api/dashboard"),
        ("app.api.router", "webhook_router", "/webhook"),
        ("app.api.router", "calendar_router", "/api/calendar"),
        ("app.api.router", "runtime_router", "/api/runtime"),
        ("app.api.router", "billing_router", "/api/billing"),
        ("app.api.router", "onboarding_router", "/api/onboarding"),
        ("app.api.router", "services_router", "/api/services"),
        ("app.api.router", "public_router", "/api/public"),
    ]
    for module, attr, prefix in router_specs:
        try:
            mod = __import__(module, fromlist=[attr])
            router = getattr(mod, attr)
            routers.append((router, prefix))
            logger.info(f"  Loaded router: {prefix}")
        except Exception as e:
            logger.warning(f"  Skipped router {prefix}: {e}")
    return routers


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting {settings.agency_name}...")

    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database init: {e}")

    try:
        from app.core.database import SessionLocal, AgentModel
        from app.agents.registry import get_all_agents
        db = SessionLocal()
        try:
            existing = db.query(AgentModel).count()
            if existing == 0:
                agents = get_all_agents()
                for a in agents:
                    db.add(AgentModel(
                        id=a.id, name=a.name, full_name=a.full_name,
                        role=a.role, title=a.title, description=a.description,
                        personality=a.personality, skills=a.skills, tools=a.tools,
                        reports_to=a.reports_to, avatar=a.avatar,
                        status=a.status, system_prompt=a.system_prompt,
                    ))
                db.commit()
                logger.info(f"Seeded {len(agents)} agents")
            else:
                logger.info(f"{existing} agents in DB")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Agent seeding: {e}")

    logger.info(f"{settings.agency_name} is ready")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.agency_name,
    description="AI Digital Marketing Agency",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router, prefix in _load_routers():
    try:
        app.include_router(router)
    except Exception as e:
        logger.warning(f"Failed to mount {prefix}: {e}")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check — NEVER crashes."""
    result = {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "agency": settings.agency_name,
        "llm_provider": settings.llm_provider,
    }
    try:
        from app.services.llm_client import llm_client
        h = await llm_client.check_health()
        result["llm_available"] = h.get("available", False)
        result["llm_model"] = h.get("model", "unknown")
    except Exception as e:
        result["llm_available"] = False
        result["llm_error"] = str(e)
    try:
        result["whatsapp_configured"] = settings.has_twilio_configured
    except:
        result["whatsapp_configured"] = False
    try:
        result["stripe_configured"] = settings.has_stripe_configured
    except:
        result["stripe_configured"] = False
    try:
        from app.agents.registry import get_agent_count
        result["agent_count"] = get_agent_count()
    except:
        result["agent_count"] = 23
    return result


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": settings.agency_name,
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
