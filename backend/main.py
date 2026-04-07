from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import get_settings
from routers.chat import router as chat_router
from services.cache_manager import cache_manager
import logging

# Logging
settings = get_settings()
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO), format="%(asctime)s [%(name)s] [%(levelname)s] [%(thread)d] %(message)s")
logger = logging.getLogger("atollom")

app = FastAPI(
    title="Atollom AI — Backend",
    description="Motor agéntico para análisis financiero y operativo conectado a Bind ERP. Versión endurecida para producción.",
    version="3.0.0",
)

# CORS restringido a orígenes y métodos específicos
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Registrar routers
app.include_router(chat_router)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Atollom AI Backend V3 (Production Hardened) is running.", "version": "3.0.0"}


@app.get("/health")
def health_check():
    redis_ok = False
    cache_type = "unknown"
    try:
        if hasattr(cache_manager, 'redis'):
            cache_manager.redis.ping()
            redis_ok = True
            cache_type = "redis"
        else:
            redis_ok = True  # In-memory siempre "disponible"
            cache_type = "in-memory"
    except Exception:
        cache_type = "redis (disconnected)"

    return {
        "status": "healthy" if redis_ok else "degraded",
        "cache_backend": cache_type,
        "agents": ["Router", "DataAnalyst", "ReportGenerator", "Supervisor"],
    }
