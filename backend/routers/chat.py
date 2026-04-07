from fastapi import APIRouter, Depends, HTTPException, status, Response
from middleware.auth import get_current_user, CurrentUser
from models.schemas import ChatRequest, ChatResponse, ResponseStatus, ChatResponseData
from services.supabase_client import get_supabase_admin
from services.bind_erp_client import BindERPClient
from services.cache_manager import cache_manager
from services.rate_limiter import rate_limiter
from agents.agent_manager import process_user_request
from config import get_settings
import logging
import uuid

logger = logging.getLogger("atollom.chat")

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Endpoint principal del chat de Atollom AI.
    Recibe un mensaje del usuario y lo procesa a través del pipeline agéntico:
    Router → DataAnalyst → ReportGenerator → Supervisor
    """
    settings = get_settings()  # noqa: F841 — usado en fallback de API key
    tenant_id = current_user.tenant_id
    trace_id = str(uuid.uuid4())
    logger.info(f"[Trace {trace_id}] Nueva petición de chat de tenant {tenant_id}")

    # 0. Verificación de Rate Limit
    rl_status = rate_limiter.check_request_limit(tenant_id)
    if not rl_status.allowed:
        return ChatResponse(
            trace_id=trace_id,
            tenant_id=tenant_id,
            status=ResponseStatus.RATE_LIMITED,
            response=ChatResponseData(content=rl_status.message),
            rate_limit_remaining=0
        )
        
    rate_limiter.increment_request(tenant_id)

    # 1. Obtener la API Key descifrada del Vault de Supabase
    supabase = get_supabase_admin()
    try:
        key_result = supabase.rpc(
            "decrypt_bind_key",
            {"p_tenant_id": tenant_id}
        ).execute()

        if not key_result.data:
            raise HTTPException(
                status_code=status.HTTP_424_FAILED_DEPENDENCY,
                detail="No se encontró una API Key de Bind ERP configurada para tu empresa.",
            )
        api_key = key_result.data
    except Exception:
        # Fallback dev: usar BIND_API_KEY_DEV del .env si está disponible
        api_key = settings.BIND_API_KEY_DEV
        if api_key:
            logger.warning(f"[Trace {trace_id}] Usando BIND_API_KEY_DEV para tenant {tenant_id} (modo dev)")
        else:
            logger.error(f"[Trace {trace_id}] Sin API Key disponible. Configura BIND_API_KEY_DEV en .env")
            raise HTTPException(
                status_code=status.HTTP_424_FAILED_DEPENDENCY,
                detail="No hay API Key de Bind ERP configurada. Contacta al administrador.",
            )

    # 2. Construir el cliente de Bind ERP con las credenciales del tenant
    bind_client = BindERPClient(tenant_id=tenant_id, api_key=api_key)

    try:
        # 3. Ejecutar el pipeline agéntico completo
        result = await process_user_request(
            user_query=request.message,
            tenant_id=tenant_id,
            bind_client=bind_client,
            cache=cache_manager,
            trace_id=trace_id,
        )
    finally:
        # Cerrar el cliente HTTP para evitar fugas de conexiones TCP
        await bind_client.close()

    # 4. Registrar el uso en usage_logs (solo llamadas reales, no cache hits)
    try:
        log_status = "cache_hit"
        if result.get("source") == "BindERP_API":
            log_status = "success"

        supabase.table("usage_logs").insert({
            "tenant_id": tenant_id,
            "endpoint_called": request.message[:100],  # Truncar para el log
            "status": log_status,
        }).execute()
    except Exception as e:
        logger.error(f"Error registrando usage_log: {e}")

    # 5. Retornar respuesta tipada
    rl_check = rate_limiter.check_request_limit(tenant_id)
    response_data = result.get("response", {})
    return ChatResponse(
        trace_id=result.get("trace_id", trace_id),
        tenant_id=tenant_id,
        intent=result.get("intent"),
        status=ResponseStatus(result.get("status", "SUCCESS")),
        response=ChatResponseData(
            content=response_data.get("content", "Sin datos disponibles."),
            chartData=response_data.get("chartData"),
            chart_type=response_data.get("chart_type"),
            insight=response_data.get("insight"),
        ),
        is_stale=result.get("is_stale", False),
        source=result.get("source"),
        rate_limit_remaining=rl_check.requests_remaining
    )
