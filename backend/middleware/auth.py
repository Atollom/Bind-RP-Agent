"""
Auth Middleware — Bind RP Agent
Soporta 3 modos en orden de prioridad:
  1. Dev bypass token (solo APP_ENV=development)
  2. JWT propio firmado por el backend (producción con Neon)
  3. JWT de Supabase (legacy, si SUPABASE_JWT_SECRET está configurado)
"""
import jwt
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from config import get_settings

logger = logging.getLogger("atollom.auth")
security = HTTPBearer()


class CurrentUser(BaseModel):
    user_id: str
    tenant_id: str
    role: str  # "admin" | "user"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    settings = get_settings()
    token = credentials.credentials

    # ── 1. Dev Bypass (demo/testing — activo si DEV_BYPASS_TOKEN está configurado) ──
    if (
        settings.DEV_BYPASS_TOKEN
        and token == settings.DEV_BYPASS_TOKEN
    ):
        logger.debug("Auth: dev bypass activo")
        return CurrentUser(user_id="dev-user-001", tenant_id="dev-tenant-001", role="admin")

    # ── 2. JWT propio del backend (Neon) ──────────────────────────
    jwt_secret = settings.JWT_SECRET or settings.SUPABASE_JWT_SECRET
    if not jwt_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El servidor no tiene configurado un secreto JWT.",
        )

    try:
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},  # audience opcional
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sesión expirada.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido.")

    user_id   = payload.get("sub") or payload.get("user_id")
    tenant_id = payload.get("tenant_id")
    role      = payload.get("role", "user")

    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token sin identificador de usuario.")

    # ── Si el JWT incluye tenant_id, confiar en él (tokens propios) ──
    if tenant_id:
        return CurrentUser(user_id=user_id, tenant_id=tenant_id, role=role)

    # ── Si no, resolver tenant desde la DB (tokens de Supabase) ──
    try:
        from services.db_client import get_user_role
        user_role = await get_user_role(user_id)
        if not user_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tu usuario no está asociado a ninguna empresa. Contacta al administrador.",
            )
        return CurrentUser(user_id=user_id, tenant_id=user_role["tenant_id"], role=user_role["role"])
    except Exception as e:
        logger.error(f"Auth: error resolviendo tenant para user {user_id}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se pudo verificar tu empresa.")
