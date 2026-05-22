"""
Fankaar Digital — Full AI Digital Marketing Agency
23 AI agents, CEO, WhatsApp, campaigns, billing
"""
import logging
import os
import threading
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ── Settings ────────────────────────────────────────────────────
class SafeSettings:
    agency_name = os.getenv("AGENCY_NAME", "Fankaar Digital")
    app_env = os.getenv("APP_ENV", "production")
    llm_provider = os.getenv("LLM_PROVIDER", "moonshot")
    database_path = os.getenv("DATABASE_PATH", "/app/data/fankaar.db")
    moonshot_api_key = os.getenv("MOONSHOT_API_KEY", "")
    moonshot_model = os.getenv("MOONSHOT_MODEL", "kimi-latest")
    owner_whatsapp = os.getenv("OWNER_WHATSAPP_NUMBER", "")
    cors_origins = ["*"]

try:
    from app.core.config import settings
    logger.info("Settings loaded from config.py")
    # Diagnostic: report moonshot_api_key presence without leaking the value
    _mk = getattr(settings, "moonshot_api_key", "")
    if _mk:
        _masked = _mk[:6] + "..." + _mk[-4:] if len(_mk) > 10 else "***"
        logger.info("Config check — moonshot_api_key: SET (masked: %s)", _masked)
    else:
        logger.warning("Config check — moonshot_api_key: EMPTY (not set in environment)")
    logger.info(
        "Config check — llm_provider=%s, moonshot_model=%s, moonshot_base_url=%s",
        getattr(settings, "llm_provider", "unknown"),
        getattr(settings, "moonshot_model", "unknown"),
        getattr(settings, "moonshot_base_url", "unknown"),
    )
except Exception as e:
    logger.error("Failed to load settings from config.py: [%s] %s", type(e).__name__, e, exc_info=True)
    logger.warning("Falling back to SafeSettings")
    settings = SafeSettings()
    _mk = settings.moonshot_api_key
    if _mk:
        _masked = _mk[:6] + "..." + _mk[-4:] if len(_mk) > 10 else "***"
        logger.info("SafeSettings check — moonshot_api_key: SET (masked: %s)", _masked)
    else:
        logger.warning("SafeSettings check — moonshot_api_key: EMPTY (MOONSHOT_API_KEY env var not set)")

# ── Create App with Lifespan ─────────────────────────────────
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start background workers on startup, clean up on shutdown."""
    logger.info("🚀 Starting Fankaar Digital background services...")
    
    # Start agent worker service (includes scheduler + runtime)
    try:
        from app.services.agent_worker import start_worker_service
        await start_worker_service()
        logger.info("✅ AgentWorkerService + APScheduler started")
    except Exception as e:
        logger.error(f"❌ Failed to start worker service: {e}")
    
    # Initialize Google Drive memory sync (restore from Drive if available)
    try:
        from app.services.google_drive_memory import DRIVE_ENABLED, restore_agent_from_drive
        from app.core.database import AgentModel, SessionLocal
        from app.core.enhanced_memory import EnhancedAgentMemory
        
        if DRIVE_ENABLED:
            db = SessionLocal()
            try:
                agents = db.query(AgentModel).all()
                restored = 0
                for agent in agents:
                    memory = EnhancedAgentMemory(agent.id)
                    if restore_agent_from_drive(agent.id, memory):
                        restored += 1
                logger.info(f"📦 Restored {restored}/{len(agents)} agents from Google Drive")
            finally:
                db.close()
    except Exception as e:
        logger.warning(f"Drive restore skipped: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Fankaar Digital services...")
    try:
        from app.services.agent_worker import stop_worker_service
        await stop_worker_service()
        logger.info("✅ AgentWorkerService stopped")
    except Exception as e:
        logger.error(f"Worker service shutdown error: {e}")

app = FastAPI(
    title=getattr(settings, 'agency_name', 'Fankaar Digital'),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Railway Domain Redirect Middleware ─────────────────────────
@app.middleware("http")
async def railway_redirect(request: Request, call_next):
    """Redirect raw Railway domains to app.fankaar.digital."""
    host = request.headers.get("host", "")
    # Redirect *.up.railway.app to canonical domain
    if host.endswith(".up.railway.app") and not request.url.path.startswith("/api/") and not request.url.path.startswith("/webhook/") and not request.url.path.startswith("/health") and not request.url.path.startswith("/docs") and not request.url.path.startswith("/redoc"):
        return JSONResponse({"message": "Please visit https://app.fankaar.digital"})
    response = await call_next(request)
    return response

# ── Health / Root ──────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "agency": getattr(settings, 'agency_name', 'Fankaar Digital'),
        "llm_provider": getattr(settings, 'llm_provider', 'moonshot'),
    }

@app.get("/api/test")
async def api_test():
    """Always works — used to verify API routing."""
    return {"api": "works", "time": datetime.utcnow().isoformat()}

@app.get("/api/debug")
async def api_debug():
    """Debug endpoint — shows startup state."""
    routes = [str(r.path) for r in app.routes if hasattr(r, 'path')]
    return {
        "routes_loaded": len(routes),
        "routes": routes[:20],
        "settings_provider": getattr(settings, 'llm_provider', 'unknown'),
        "settings_has_moonshot_key": bool(getattr(settings, 'moonshot_api_key', '')),
    }

@app.get("/api/diagnose")
async def api_diagnose():
    """Diagnose why routers failed to load."""
    import importlib, traceback
    router_map = {
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
        "approvals": ("app.api.router", "approval_router"),
    }
    results = {}
    for name, (mod_path, attr) in router_map.items():
        try:
            mod = importlib.import_module(mod_path)
            router = getattr(mod, attr)
            results[name] = {"status": "ok", "routes": len(router.routes) if hasattr(router, 'routes') else 'unknown'}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e), "traceback": traceback.format_exc()}
    return results

@app.get("/")
async def root():
    # In Docker, frontend is at /app/frontend/
    paths = [
        "frontend/index.html",
        "/app/frontend/index.html",
        "../frontend/index.html",
    ]
    for p in paths:
        if os.path.exists(p):
            return FileResponse(p)

    return {
        "name": getattr(settings, 'agency_name', 'Fankaar Digital'),
        "version": "1.0.0",
        "health": "/health",
        "docs": "/docs",
        "api": "/api",
        "message": "Frontend not found at expected paths"
    }

# Load All Routers - defined later

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
        "approvals": ("app.api.router", "approval_router", "/api/approvals"),
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

# Mount static files after routers to avoid overriding API paths
try:
    static_paths = [
        ("frontend", "frontend"),
        ("/app/frontend", "frontend"),
        ("../frontend", "frontend"),
    ]
    mounted = False
    for static_dir, name in static_paths:
        if os.path.exists(static_dir):
            app.mount("/static", StaticFiles(directory=static_dir), name=f"{name}_static")
            app.mount("/", StaticFiles(directory=static_dir, html=True), name=name)
            logger.info(f"Mounted static files from {static_dir}")
            mounted = True
            break
    if not mounted:
        logger.warning("No frontend static files found to mount")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")

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

bg_init()
logger.info("App startup complete — waiting for requests")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
