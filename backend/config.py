from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Configuración central de Atollom AI Backend — V3 Producción."""

    # --- Base de Datos (Neon PostgreSQL — reemplaza Supabase DB) ---
    # Obtener en: neon.tech → proyecto → Connection String
    DATABASE_URL: str = ""  # postgresql://user:pass@host/dbname?sslmode=require
    JWT_SECRET: str = ""    # Clave para firmar/verificar tokens JWT propios

    # --- Supabase (opcional, legacy) ---
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # --- Bind ERP ---
    BIND_API_BASE_URL: str = "https://api.bind.com.mx/api"

    # --- Gemini AI (cerebro del agente) ---
    # Modelo primario: gemini-2.5-flash-lite (RPD ILIMITADO — ideal para 600 tenants)
    # Modelo análisis: gemini-2.5-flash (10K RPD — para análisis complejos)
    GEMINI_API_KEY: str = ""
    GEMINI_PRIMARY_MODEL: str = "gemini-2.5-flash-lite"  # Ilimitado RPD
    GEMINI_ANALYSIS_MODEL: str = "gemini-2.5-flash"      # Análisis profundo
    GEMINI_MAX_TOKENS: int = 2048
    GEMINI_TEMPERATURE: float = 0.2   # Bajo = datos exactos, sin alucinaciones

    # --- Redis (Caché + Rate Limiting) ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300
    CACHE_GRACE_PERIOD_SECONDS: int = 86400

    # --- Rate Limiting por Tenant (600 clientes) ---
    RATE_LIMIT_MAX_REQUESTS_PER_DAY: int = 200
    RATE_LIMIT_MAX_BIND_CALLS_PER_DAY: int = 50

    # --- Dev Testing ---
    BIND_API_KEY_DEV: str = ""
    DEV_BYPASS_TOKEN: str = ""

    # --- App ---
    APP_ENV: str = "development"
    APP_ENCRYPTION_KEY: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
