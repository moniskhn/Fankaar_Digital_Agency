"""
Claude Mythos — FastAPI Entry Point
"""
import logging
import os
import threading
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Safe Settings ───────────────────────────────────────────────
class SafeSettings:
    agency_name = os.getenv("AGENCY_NAME", "Claude Mythos")
    app_env = os.getenv("APP_ENV", "production")
    llm_provider = os.getenv("LLM_PROVIDER", "moonshot")
    database_path = os.getenv("DATABASE_PATH", "/app/data/mythos.db")
    cors_origins = ["*"]

try:
    from app.core.config import settings
    logger.info("Settings loaded from config.py")
except Exception as e:
    logger.warning(f"Using safe settings: {e}")
    settings = SafeSettings()

# ── Create App ─────────────────────────────────────────────────
app = FastAPI(title=settings.agency_name, version="1.0.0", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ── Health ─────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0", "timestamp": datetime.utcnow().isoformat(), "agency": getattr(settings, 'agency_name', 'Claude Mythos')}

@app.get("/")
async def root():
    return {"name": getattr(settings, 'agency_name', 'Claude Mythos'), "version": "1.0.0", "health": "/health", "docs": "/docs"}

logger.info("FastAPI app created")

# ── Load Routers ───────────────────────────────────────────────
def load_routers():
    routers = {
        "agents": ("app.api.router", "agents_router"),
        "campaigns": ("app.api.router", "campaigns_router"),
        "ceo": ("app.api.router", "ceo_router"),
        "clients": ("app.api.router", "clients_router"),
        "regional": ("app.api.router", "regional_router"),
        "dashboard": ("app.api.router", "dashboard_router"),
        "webhook": ("app.api.router", "webhook_router"),
        "calendar": ("app.api.router", "calendar_router"),
        "runtime": ("app.api.router", "runtime_router"),
        "billing": ("app.api.router", "billing_router"),
        "onboarding": ("app.api.router", "onboarding_router"),
        "services": ("app.api.router", "services_router"),
        "public": ("app.api.router", "public_router"),
    }
    loaded = 0
    for name, (mod, attr) in routers.items():
        try:
            m = __import__(mod, fromlist=[attr])
            app.include_router(getattr(m, attr))
            loaded += 1
            logger.info(f"  OK {name}")
        except Exception as e:
            logger.warning(f"  SKIP {name}: {e}")
    logger.info(f"Loaded {loaded}/{len(routers)} routers")

load_routers()

# ── Background Init ────────────────────────────────────────────
def bg_init():
    try:
        from app.core.database import init_db
        init_db()
        logger.info("Database OK")
    except Exception as e:
        logger.warning(f"Database: {e}")
    try:
        from app.core.database import SessionLocal, AgentModel
        from app.agents.registry import get_all_agents
        db = SessionLocal()
        try:
            if db.query(AgentModel).count() == 0:
                for a in get_all_agents():
                    db.add(AgentModel(id=a.id, name=a.name, full_name=a.full_name, role=a.role, title=a.title, description=a.description, personality=a.personality, skills=a.skills, tools=a.tools, reports_to=a.reports_to, avatar=a.avatar, status=a.status, system_prompt=a.system_prompt))
                db.commit()
                logger.info("Agents seeded")
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"Agents: {e}")

threading.Thread(target=bg_init, daemon=True).start()
logger.info("App ready")
