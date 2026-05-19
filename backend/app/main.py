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

# ── Create App ─────────────────────────────────────────────────
app = FastAPI(
    title=getattr(settings, 'agency_name', 'Fankaar Digital'),
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
