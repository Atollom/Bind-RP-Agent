from pydantic import BaseModel, Field
from typing import Optional, Any
from enum import Enum


class ChatRequest(BaseModel):
    """Petición del usuario al chat de Atollom AI."""
    message: str


class ResponseStatus(str, Enum):
    """Estado de la respuesta del pipeline agéntico."""
    SUCCESS = "SUCCESS"
    DEGRADED_CACHE = "DEGRADED_CACHE"
    RATE_LIMITED = "RATE_LIMITED"
    ERROR = "ERROR"
    REJECTED = "REJECTED"
    AMBIGUOUS = "AMBIGUOUS"


class ChatResponseData(BaseModel):
    """Datos de la respuesta para el frontend (contenido + visual)."""
    content: str
    chartData: Optional[list[dict[str, Any]]] = None
    chart_type: Optional[str] = None  # "bar" | "line" | "pie" | "area"
    insight: Optional[str] = None     # Micro-insight de negocio


class ChatResponse(BaseModel):
    """
    Respuesta completa del sistema agéntico — formato enterprise.
    Incluye trazabilidad, costo estimado y datos para el frontend.
    """
    # --- Trazabilidad ---
    trace_id: str                                 # UUID v4 generado por el Router
    tenant_id: Optional[str] = None               # ID del cliente

    # --- Clasificación ---
    intent: Optional[str] = None                  # "VENTAS" | "INVENTARIO" | etc.
    status: ResponseStatus = ResponseStatus.SUCCESS

    # --- Control de Costos ---
    cost_estimate_usd: float = 0.0                # Calculado por el Supervisor
    is_model_failover: bool = False               # Si se usó BACKUP_MODEL

    # --- Datos del Reporte ---
    response: ChatResponseData

    # --- Metadata de Caché ---
    is_stale: bool = False
    source: Optional[str] = None                  # "Cache" | "BindERP_API" | "Cache (Stale)"

    # --- Rate Limit Info (para headers del frontend) ---
    rate_limit_remaining: Optional[int] = None


class HealthResponse(BaseModel):
    status: str
    message: str
    agents: list[str] = []


class UsageResponse(BaseModel):
    """Uso actual del tenant — para dashboards de admin."""
    tenant_id: str
    requests_used: int
    requests_limit: int
    bind_calls_used: int
    bind_calls_limit: int
