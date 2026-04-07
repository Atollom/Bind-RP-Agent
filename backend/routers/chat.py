from fastapi import APIRouter, Depends, HTTPException, status
from middleware.auth import get_current_user, CurrentUser
from models.schemas import ChatRequest, ChatResponse, ResponseStatus, ChatResponseData
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
    settings = get_settings()
    tenant_id = current_user.tenant_id
    trace_id = str(uuid.uuid4())
    logger.info(f"[Trace {trace_id}] Tenant {tenant_id} → chat")

    # 0. Rate limit
    rl_status = rate_limiter.check_request_limit(tenant_id)
    if not rl_status.allowed:
        return ChatResponse(
            trace_id=trace_id, tenant_id=tenant_id,
            status=ResponseStatus.RATE_LIMITED,
            response=ChatResponseData(content=rl_status.message),
            rate_limit_remaining=0,
        )
    rate_limiter.increment_request(tenant_id)

    # 1. Obtener API Key de Bind ERP
    # Primero: Neon vault (producción)
    # Fallback: BIND_API_KEY_DEV del .env (dev/testing)
    api_key = None
    try:
        from services.db_client import get_bind_api_key
        api_key = await get_bind_api_key(tenant_id, settings.APP_ENCRYPTION_KEY)
    except Exception:
        pass  # DB no configurada aún → usar fallback dev

    if not api_key:
        api_key = settings.BIND_API_KEY_DEV
        if api_key:
            logger.warning(f"[Trace {trace_id}] Usando BIND_API_KEY_DEV (modo dev)")
        else:
            raise HTTPException(
                status_code=status.HTTP_424_FAILED_DEPENDENCY,
                detail="No hay API Key de Bind ERP configurada para tu empresa.",
            )

    # 2. Pipeline agéntico: Router → DataAnalyst → ReportGenerator → Supervisor
    bind_client = BindERPClient(tenant_id=tenant_id, api_key=api_key)
    try:
        result = await process_user_request(
            user_query=request.message,
            tenant_id=tenant_id,
            bind_client=bind_client,
            cache=cache_manager,
            trace_id=trace_id,
        )
    finally:
        await bind_client.close()

    # 3. Log de uso (falla silenciosamente si DB no está lista)
    try:
        from services.db_client import log_usage
        log_status = "success" if result.get("source") == "BindERP_API" else "cache_hit"
        await log_usage(tenant_id, request.message[:100], log_status)
    except Exception as e:
        logger.error(f"[Trace {trace_id}] Error en usage_log: {e}")

    # 4. Respuesta
    rl_check = rate_limiter.check_request_limit(tenant_id)
    resp = result.get("response", {})
    return ChatResponse(
        trace_id=result.get("trace_id", trace_id),
        tenant_id=tenant_id,
        intent=result.get("intent"),
        status=ResponseStatus(result.get("status", "SUCCESS")),
        response=ChatResponseData(
            content=resp.get("content", "Sin datos disponibles."),
            chartData=resp.get("chartData"),
            chart_type=resp.get("chart_type"),
            insight=resp.get("insight"),
        ),
        is_stale=result.get("is_stale", False),
        source=result.get("source"),
        rate_limit_remaining=rl_check.requests_remaining,
    )
