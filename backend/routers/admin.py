"""
Admin Router — Gestión de clientes Bind ERP (solo rol admin)
POST /api/admin/clients  → registrar nuevo cliente con su API Key de Bind
GET  /api/admin/clients  → listar todos los clientes
"""
import logging
import bcrypt
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from config import get_settings
from middleware.auth import get_current_user, CurrentUser

logger = logging.getLogger("atollom.admin")
router = APIRouter(prefix="/api/admin", tags=["Admin"])


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acceso restringido a administradores.")
    return current_user


class NewClientRequest(BaseModel):
    company_name: str
    email: str
    password: str
    bind_api_key: str


class ClientResponse(BaseModel):
    tenant_id: str
    company_name: str
    email: str
    created_at: str


@router.post("/clients", response_model=ClientResponse, status_code=201)
async def create_client(
    req: NewClientRequest,
    admin: CurrentUser = Depends(require_admin),
):
    """Registra un nuevo cliente: crea tenant, usuario y guarda su API Key de Bind cifrada."""
    settings = get_settings()

    try:
        from services.db_client import get_pool, store_bind_api_key
        pool = await get_pool()
        async with pool.acquire() as conn:
            # 1. Crear tenant
            tenant = await conn.fetchrow(
                "INSERT INTO public.tenants (name) VALUES ($1) RETURNING id, name, created_at",
                req.company_name
            )

            # 2. Crear usuario con contraseña hasheada
            hashed = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt()).decode()
            existing = await conn.fetchrow("SELECT id FROM public.users WHERE email=$1", req.email)
            if existing:
                raise HTTPException(status_code=400, detail=f"El email {req.email} ya está registrado.")

            user = await conn.fetchrow(
                "INSERT INTO public.users (email, hashed_password) VALUES ($1, $2) RETURNING id",
                req.email, hashed
            )

            # 3. Asignar rol admin al cliente (puede cambiarse a 'user' si se prefiere)
            await conn.execute(
                "INSERT INTO public.user_roles (user_id, tenant_id, role) VALUES ($1, $2, 'admin')",
                user["id"], tenant["id"]
            )

        # 4. Guardar API Key de Bind cifrada (fuera del bloque anterior para evitar TX largas)
        await store_bind_api_key(str(tenant["id"]), req.bind_api_key, settings.APP_ENCRYPTION_KEY)

        logger.info(f"[Admin {admin.user_id}] Cliente creado: {req.company_name} ({tenant['id']})")

        return ClientResponse(
            tenant_id=str(tenant["id"]),
            company_name=tenant["name"],
            email=req.email,
            created_at=str(tenant["created_at"]),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"create_client error: {e}")
        raise HTTPException(status_code=500, detail="Error al registrar el cliente. Intenta de nuevo.")


@router.get("/clients")
async def list_clients(admin: CurrentUser = Depends(require_admin)):
    """Lista todos los tenants/clientes registrados."""
    try:
        from services.db_client import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT t.id, t.name, t.created_at,
                          u.email,
                          EXISTS(SELECT 1 FROM public.bind_erp_keys b WHERE b.tenant_id = t.id) as has_bind_key
                   FROM public.tenants t
                   LEFT JOIN public.user_roles ur ON ur.tenant_id = t.id AND ur.role = 'admin'
                   LEFT JOIN public.users u ON u.id = ur.user_id
                   ORDER BY t.created_at DESC"""
            )
        return [
            {
                "tenant_id": str(r["id"]),
                "company_name": r["name"],
                "email": r["email"],
                "has_bind_key": r["has_bind_key"],
                "created_at": str(r["created_at"]),
            }
            for r in rows
        ]
    except Exception as e:
        logger.error(f"list_clients error: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener clientes.")
