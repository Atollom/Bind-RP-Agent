from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Configuración central de Atollom AI Backend — V3 Producción."""

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    # --- Bind ERP ---
    BIND_API_BASE_URL: str = "https://api.bind.com.mx/api"

    # --- Redis (Caché Persistente + Rate Limiting) ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_TTL_SECONDS: int = 300            # 5 min = dato fresco
    CACHE_GRACE_PERIOD_SECONDS: int = 86400  # 24h = modo contingencia

    # --- Rate Limiting por Tenant ---
    RATE_LIMIT_MAX_REQUESTS_PER_DAY: int = 200   # Max requests por tenant/día
    RATE_LIMIT_MAX_BIND_CALLS_PER_DAY: int = 50  # Max API calls a Bind por tenant/día

    # --- LLM / Modelos de IA (preparado para integración futura) ---
    LLM_PROVIDER: str = "none"                    # "none" | "openai" | "anthropic"
    LLM_PRIMARY_MODEL: str = ""                   # ej. "gpt-4o", "claude-sonnet-4-20250514"
    LLM_BACKUP_MODEL: str = ""                    # Failover automático
    LLM_API_KEY: str = ""                         # API Key del proveedor de IA
    LLM_MAX_TOKENS: int = 1024
    LLM_TEMPERATURE: float = 0.3                  # Bajo = respuestas más deterministas

    # --- Costos (estimación por request) ---
    COST_PER_1K_INPUT_TOKENS: float = 0.005       # USD, se ajusta por modelo
    COST_PER_1K_OUTPUT_TOKENS: float = 0.015

    # --- Dev Testing (SOLO para desarrollo, remover en producción) ---
    BIND_API_KEY_DEV: str = ""    # API Key de Bind para pruebas locales
    DEV_BYPASS_TOKEN: str = ""    # Token especial que bypasea JWT en APP_ENV=development

    # --- App ---
    APP_ENV: str = "development"                  # "development" | "production"
    APP_ENCRYPTION_KEY: str = ""  # Clave maestra para pgcrypto en el Vault
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
