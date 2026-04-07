from supabase import create_client, Client
from functools import lru_cache
from config import get_settings


@lru_cache()
def get_supabase_admin() -> Client:
    """
    Cliente Supabase con service_role para operaciones privilegiadas del backend.
    SOLO debe usarse en el servidor (FastAPI). Tiene acceso completo al Vault y bypass de RLS.
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


@lru_cache()
def get_supabase_public() -> Client:
    """
    Cliente Supabase con anon key. Respeta RLS.
    Usado para operaciones del lado del usuario autenticado.
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
