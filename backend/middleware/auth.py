import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
from config import get_settings
from services.supabase_client import get_supabase_admin


security = HTTPBearer()


class CurrentUser(BaseModel):
    """Representa al usuario autenticado con su contexto multi-tenant."""
    user_id: str
    tenant_id: str
    role: str  # "admin" | "user"


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> CurrentUser:
    """
    Middleware de autenticación para FastAPI.
    1. Extrae el JWT del header Authorization: Bearer <token>
    2. Lo valida contra el JWT Secret de Supabase
    3. Resuelve el tenant_id del usuario desde user_roles
    4. Retorna un objeto CurrentUser seguro
    """
    settings = get_settings()
    token = credentials.credentials

    # DEV BYPASS: Solo activo en APP_ENV=development con token especial
    if (
        settings.APP_ENV == "development"
        and settings.DEV_BYPASS_TOKEN
        and token == settings.DEV_BYPASS_TOKEN
    ):
        return CurrentUser(user_id="dev-user-001", tenant_id="dev-tenant-001", role="admin")

    # 1. Decodificar y validar el JWT
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada. Por favor, inicia sesión nuevamente.",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticación inválido.",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token no contiene identificador de usuario.",
        )

    # 2. Resolver tenant_id desde la base de datos
    supabase = get_supabase_admin()
    result = (
        supabase.table("user_roles")
        .select("tenant_id, role")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu usuario no está asociado a ninguna empresa. Contacta al administrador.",
        )

    user_role = result.data[0]

    return CurrentUser(
        user_id=user_id,
        tenant_id=user_role["tenant_id"],
        role=user_role["role"],
    )
