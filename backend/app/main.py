"""
Claude Mythos — Full AI Digital Marketing Agency
23 AI agents, CEO, WhatsApp, campaigns, billing
"""
import logging
import os
import threading
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Settings ────────────────────────────────────────────────────
class SafeSettings:
    agency_name = os.getenv("AGENCY_NAME", "Claude Mythos")
    app_env = os.getenv("APP_ENV", "production")
    llm_provider = os.getenv("LLM_PROVIDER", "moonshot")
    database_path = os.getenv("DATABASE_PATH", "/app/data/mythos.db")
    moonshot_api_key = os.getenv("MOONSHOT_API_KEY", "")
    moonshot_model = os.getenv("MOONSHOT_MODEL", "kimi-latest")
    owner_whatsapp = os.getenv("OWNER_WHATSAPP_NUMBER", "")
    cors_origins = ["*"]

try:
    from app.core.config import settings
    logger.info("Settings loaded from config.py")
except Exception as e:
    logger.warning(f"Using safe settings: {e}")
    settings = SafeSettings()

# ── Create App ─────────────────────────────────────────────────
app = FastAPI(
    title=getattr(settings, 'agency_name', 'Claude Mythos'),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Health / Root ──────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "agency": getattr(settings, 'agency_name', 'Claude Mythos'),
        "llm_provider": getattr(settings, 'llm_provider', 'moonshot'),
    }

@app.get("/")
async def root():
    return {
        "name": getattr(settings, 'agency_name', 'Claude Mythos'),
        "version": "1.0.0",
        "health": "/health",
        "docs": "/docs",
        "api": "/api",
    }

logger.info("FastAPI app created")

# ── Load All Routers ───────────────────────────────────────────
def load_routers():
    router_map = {
        "agents": ("app.api.router", "agents_router", "/api/agents"),
        "campaigns": ("app.api.router", "campaigns_router", "/api/campaigns"),
        "ceo": ("app.api.router", "ceo_router", "/api/ceo"),
        "clients": ("app.api.router", "clients_router", "/api/clients"),
        "regional": ("app.api.router", "regional_router", "/api/regional"),
        "dashboard": ("app.api.router", "dashboard_router", "/api/dashboard"),
        "webhook": ("app.api.router", "webhook_router", "/webhook"),
        "calendar": ("app.api.router", "calendar_router", "/api/calendar"),
        "runtime": ("app.api.router", "runtime_router", "/api/runtime"),
        "billing": ("app.api.router", "billing_router", "/api/billing"),
        "onboarding": ("app.api.router", "onboarding_router", "/api/onboarding"),
        "services": ("app.api.router", "services_router", "/api/services"),
        "public": ("app.api.router", "public_router", "/api/public"),
    }
    loaded = 0
    for name, (mod_path, attr, prefix) in router_map.items():
        try:
            mod = __import__(mod_path, fromlist=[attr])
            router = getattr(mod, attr)
            app.include_router(router)
            loaded += 1
            logger.info(f"  ✅ {name}: {prefix}")
        except Exception as e:
            logger.warning(f"  ⚠️  {name}: {e}")
    logger.info(f"Loaded {loaded}/{len(router_map)} routers")

load_routers()

# ── Background DB Init ─────────────────────────────────────────
def bg_init():
    try:
        from app.core.database import init_db
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(f"Database init: {e}")

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
                        id=a.id,
                        name=a.name,
                        full_name=a.full_name,
                        role=a.role,
                        title=a.title,
                        description=a.description,
                        personality=a.personality,
                        skills=a.skills,
                        tools=a.tools,
                        reports_to=a.reports_to,
                        avatar=a.avatar,
                        status=a.status,
                        system_prompt=a.system_prompt,
                    ))
                db.commit()
                logger.info(f"Seeded {len(agents)} agents")
            else:
                logger.info(f"{existing} agents already in DB")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Agent seeding: {e}")

    logger.info("Background init complete")

threading.Thread(target=bg_init, daemon=True).start()
logger.info("App startup complete — waiting for requests")
