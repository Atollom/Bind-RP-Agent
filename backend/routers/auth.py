"""
Auth Router — Login con JWT propio (sin Supabase)
POST /api/auth/login  → retorna access_token
POST /api/auth/register → crea usuario (solo en dev por ahora)
"""
import jwt
import bcrypt
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from config import get_settings

logger = logging.getLogger("atollom.auth_router")
router = APIRouter(prefix="/api/auth", tags=["Auth"])

TOKEN_EXPIRE_HOURS = 24 * 7  # 7 días


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    tenant_name: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _create_token(user_id: str, tenant_id: str, role: str) -> str:
    settings = get_settings()
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    settings = get_settings()

    # Dev bypass: email+password especiales para testing
    if req.email == "dev@atollom.ai" and req.password == "dev2025" and settings.DEV_BYPASS_TOKEN:
        token = _create_token("dev-user-001", "dev-tenant-001", "admin") if settings.JWT_SECRET else settings.DEV_BYPASS_TOKEN
        return TokenResponse(access_token=token)

    # Producción: verificar en Neon
    try:
        from services.db_client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT u.id, u.hashed_password, ur.tenant_id, ur.role
                   FROM public.users u
                   JOIN public.user_roles ur ON ur.user_id = u.id
                   WHERE u.email = $1 AND u.is_active = TRUE
                   LIMIT 1""",
                req.email
            )
    except Exception as e:
        logger.error(f"Login DB error: {e}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Servicio no disponible.")

    if not row or not bcrypt.checkpw(req.password.encode(), row["hashed_password"].encode()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas.")

    token = _create_token(str(row["id"]), str(row["tenant_id"]), row["role"])
    return TokenResponse(access_token=token)


@router.post("/register", response_model=TokenResponse)
async def register(req: RegisterRequest):
    """Crea un tenant + usuario admin. Solo disponible en development."""
    settings = get_settings()
    if settings.APP_ENV != "development":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Registro no disponible en producción.")

    try:
        from services.db_client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            # Crear tenant
            tenant = await conn.fetchrow(
                "INSERT INTO public.tenants (name) VALUES ($1) RETURNING id", req.tenant_name
            )
            # Crear usuario
            hashed = pwd_context.hash(req.password)
            user = await conn.fetchrow(
                "INSERT INTO public.users (email, hashed_password) VALUES ($1, $2) RETURNING id",
                req.email, hashed
            )
            # Asignar rol admin
            await conn.execute(
                "INSERT INTO public.user_roles (user_id, tenant_id, role) VALUES ($1, $2, 'admin')",
                user["id"], tenant["id"]
            )
    except Exception as e:
        logger.error(f"Register error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error al registrar: {e}")

    token = _create_token(str(user["id"]), str(tenant["id"]), "admin")
    return TokenResponse(access_token=token)
