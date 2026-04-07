"""
DB Client — Neon PostgreSQL (reemplaza Supabase para la capa de datos)
Usa asyncpg para operaciones async + psycopg2 para operaciones de migración sync.

Neon es PostgreSQL estándar: todas las migraciones SQL existentes funcionan sin cambios.
Setup: neon.tech → crear proyecto → copiar DATABASE_URL en .env
"""
import asyncpg
import logging
from typing import Any, Dict, List, Optional
from functools import lru_cache

from config import get_settings

logger = logging.getLogger("atollom.db")

# ====================================================================
# POOL DE CONEXIONES ASYNCPG (singleton)
# ====================================================================
_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None or _pool._closed:
        settings = get_settings()
        if not settings.DATABASE_URL:
            raise RuntimeError("DATABASE_URL no está configurado en .env")
        _pool = await asyncpg.create_pool(
            dsn=settings.DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        logger.info("Pool de conexiones Neon inicializado.")
    return _pool


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


# ====================================================================
# OPERACIONES: TENANTS
# ====================================================================
async def get_tenant_by_id(tenant_id: str) -> Optional[Dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, created_at FROM public.tenants WHERE id = $1",
            tenant_id
        )
        return dict(row) if row else None


async def create_tenant(name: str) -> Dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "INSERT INTO public.tenants (name) VALUES ($1) RETURNING id, name, created_at",
            name
        )
        return dict(row)


# ====================================================================
# OPERACIONES: USER ROLES
# ====================================================================
async def get_user_role(user_id: str) -> Optional[Dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT tenant_id, role FROM public.user_roles WHERE user_id = $1 LIMIT 1",
            user_id
        )
        return dict(row) if row else None


async def create_user_role(user_id: str, tenant_id: str, role: str = "user") -> Dict:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO public.user_roles (user_id, tenant_id, role)
               VALUES ($1, $2, $3)
               ON CONFLICT (user_id, tenant_id) DO UPDATE SET role = EXCLUDED.role
               RETURNING id, user_id, tenant_id, role""",
            user_id, tenant_id, role
        )
        return dict(row)


# ====================================================================
# OPERACIONES: USUARIOS (auth propio, sin Supabase)
# ====================================================================
async def get_user_by_email(email: str) -> Optional[Dict]:
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, email, hashed_password FROM public.users WHERE email = $1",
            email
        )
        return dict(row) if row else None


# ====================================================================
# OPERACIONES: API KEYS DE BIND ERP (cifradas con pgcrypto)
# ====================================================================
async def store_bind_api_key(tenant_id: str, api_key: str, encryption_key: str) -> None:
    """Guarda la API Key de Bind cifrada con pgcrypto."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO api_keys_private.bind_erp_keys (tenant_id, encrypted_token)
               VALUES ($1, pgp_sym_encrypt($2, $3))
               ON CONFLICT (tenant_id) DO UPDATE
               SET encrypted_token = pgp_sym_encrypt($2, $3), updated_at = NOW()""",
            tenant_id, api_key, encryption_key
        )


async def get_bind_api_key(tenant_id: str, encryption_key: str) -> Optional[str]:
    """Recupera y descifra la API Key de Bind."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """SELECT pgp_sym_decrypt(encrypted_token::bytea, $1) as api_key
               FROM api_keys_private.bind_erp_keys
               WHERE tenant_id = $2""",
            encryption_key, tenant_id
        )
        return row["api_key"] if row else None


# ====================================================================
# OPERACIONES: USAGE LOGS
# ====================================================================
async def log_usage(tenant_id: str, endpoint: str, status: str) -> None:
    """Registra el uso del sistema por tenant. Falla silenciosamente."""
    try:
        pool = await get_pool()
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO public.usage_logs (tenant_id, endpoint_called, status)
                   VALUES ($1, $2, $3)""",
                tenant_id, endpoint[:100], status
            )
    except Exception as e:
        logger.error(f"Error registrando usage_log: {e}")
