"""
Pipeline Agéntico — Bind RP Agent (Atollom AI)
Arquitectura: Router → DataAnalyst → ReportGenerator → Supervisor

Cerebro: Gemini 2.0 Flash (RPD ilimitado) + Gemini 2.5 Flash (análisis profundo)
Diseñado para 600 tenants simultáneos de Bind ERP.
"""
from typing import Dict, Any
import logging

from services.gemini_client import (
    classify_intent_with_gemini,
    analyze_erp_data,
    suggest_chart_config,
)

logger = logging.getLogger("atollom.agents")


# =====================================================================
# AGENT 1: ROUTER AGENT
# Clasificación rápida por keywords → Gemini como fallback inteligente
# =====================================================================
class RouterAgent:
    MODULES = {
        "VENTAS": [
            "venta", "ventas", "factura", "facturas", "facturación", "facturamos",
            "revenue", "ingreso", "ingresos", "vendimos", "cobrar", "cobro",
            "cotización", "cotizaciones", "pedido", "pedidos", "cobrada",
            "cuentas por cobrar", "pago recibido", "pagos recibidos",
        ],
        "INVENTARIO": [
            "inventario", "stock", "existencia", "existencias", "almacén",
            "almacenes", "producto", "productos", "sku", "artículo", "artículos",
            "rotación", "movimiento", "ajuste", "entrada", "salida",
        ],
        "COMPRAS": [
            "compra", "compras", "proveedor", "proveedores", "orden de compra",
            "cuentas por pagar", "gasto", "gastos", "recepción",
        ],
        "CONTABILIDAD": [
            "contabilidad", "balance", "estado financiero", "póliza", "pólizas",
            "catálogo de cuentas", "asiento", "contable", "fiscal",
            "impuesto", "impuestos", "iva", "isr", "cfdi",
        ],
        "DIRECTORIO": [
            "directorio", "contacto", "contactos", "rfc", "razón social",
        ],
    }

    # Palabras clave que indican que el usuario quiere un análisis financiero
    # (útiles para pasar al fallback de Gemini en lugar de REJECT)
    FINANCIAL_CLUES = [
        "cuánto", "cuanto", "total", "resumen", "reporte", "métrica", "métricas",
        "análisis", "analisis", "comparar", "comparativo", "tendencia", "tendencias",
        "este mes", "mes pasado", "año pasado", "año anterior", "semana",
        "mejor", "peor", "top", "más vendido", "más comprado",
        "rendimiento", "rentabilidad", "utilidad", "margen",
    ]

    IRRELEVANT_PATTERNS = [
        "chiste", "clima", "cuento", "receta", "deporte", "película",
        "canción", "opinión personal", "qué hora es", "dime algo",
    ]

    async def route(self, user_query: str) -> Dict[str, str]:
        query_lower = user_query.lower().strip()

        # Filtro de irrelevancia explícita
        if any(kw in query_lower for kw in self.IRRELEVANT_PATTERNS):
            return {
                "intent": "REJECT",
                "message": (
                    "Soy Atollom AI, tu asistente de inteligencia financiera conectado a Bind ERP. "
                    "Puedo ayudarte con Ventas, Inventario, Compras, Contabilidad o tu Directorio. "
                    "¿En qué módulo deseas profundizar?"
                ),
            }

        # Clasificación rápida por keywords
        matched = []
        for module, keywords in self.MODULES.items():
            if any(kw in query_lower for kw in keywords):
                matched.append(module)

        if len(matched) == 1:
            return {"intent": matched[0]}
        if len(matched) > 1:
            # Priorizar el primero que matcheó
            return {"intent": matched[0]}

        # Si tiene pistas financieras, usar Gemini para clasificar
        has_financial_clue = any(clue in query_lower for clue in self.FINANCIAL_CLUES)
        if has_financial_clue or len(user_query) > 15:
            logger.info("RouterAgent → delegando clasificación a Gemini")
            return await classify_intent_with_gemini(user_query)

        return {
            "intent": "AMBIGUOUS",
            "message": (
                "No logré identificar tu consulta. ¿Es sobre Ventas, Inventario, "
                "Compras, Contabilidad o Directorio?"
            ),
        }


# =====================================================================
# AGENT 2: DATA ANALYST AGENT
# Guardián de Bind ERP: caché primero, API solo en cache miss
# =====================================================================
class DataAnalystAgent:
    INTENT_TO_ENDPOINT = {
        "VENTAS":       "get_invoices",
        "INVENTARIO":   "get_inventory",
        "COMPRAS":      "get_purchase_orders",
        "CONTABILIDAD": "get_accounts",
        "DIRECTORIO":   "get_clients",
    }

    MAX_API_CALLS_PER_QUERY = 2  # Guardrail anti-alucinación

    def __init__(self, bind_client, cache):
        self.bind_client = bind_client
        self.cache = cache

    async def fetch_data(self, intent: str, session_calls: int = 0) -> Dict[str, Any]:
        if session_calls >= self.MAX_API_CALLS_PER_QUERY:
            logger.warning(f"[Tenant {self.bind_client.tenant_id}] MAX_API_CALLS alcanzado.")
            return {"status": "error", "message": "Límite de seguridad alcanzado para proteger tu cuota de Bind ERP."}

        cache_key = f"endpoint_{intent}"
        cached = self.cache.get(self.bind_client.tenant_id, cache_key)

        if cached["data"]:
            source = "Cache (Stale)" if cached["is_stale"] else "Cache"
            logger.info(f"[Tenant {self.bind_client.tenant_id}] {source} hit → {intent}")
            return {"status": "success", "source": source, "is_stale": cached["is_stale"], "data": cached["data"]}

        method_name = self.INTENT_TO_ENDPOINT.get(intent, "get_invoices")
        erp_method = getattr(self.bind_client, method_name, None)

        if erp_method:
            logger.info(f"[Tenant {self.bind_client.tenant_id}] Cache MISS → Bind ERP: {method_name}")
            erp_response = await erp_method()

            if isinstance(erp_response, dict) and erp_response.get("error"):
                logger.error(f"[Tenant {self.bind_client.tenant_id}] Bind error: {erp_response}")
                if cached["data"]:
                    return {"status": "success", "source": "Cache (Degradado)", "is_stale": True, "data": cached["data"]}
                return {"status": "error", "message": erp_response.get("message", "Error al consultar Bind ERP.")}

            self.cache.set(self.bind_client.tenant_id, cache_key, erp_response)
            return {"status": "success", "source": "BindERP_API", "is_stale": False, "data": erp_response}

        return {"status": "error", "message": f"El módulo '{intent}' no tiene endpoint configurado."}


# =====================================================================
# AGENT 3: REPORT GENERATOR AGENT
# Transforma datos crudos en análisis ejecutivo con Gemini
# =====================================================================
class ReportGeneratorAgent:
    async def format_for_frontend(
        self,
        raw_data: Dict[str, Any],
        intent: str,
        user_query: str,
    ) -> Dict[str, Any]:
        data_list = raw_data.get("data", [])
        if not isinstance(data_list, list):
            data_list = []

        # Determinar si usar análisis profundo (gemini-2.5-flash)
        # Solo para consultas largas o comparativos
        use_deep = len(user_query) > 60 or any(
            kw in user_query.lower() for kw in ["comparativo", "año pasado", "tendencia", "reporte", "análisis"]
        )

        # Gemini genera el análisis ejecutivo
        content = await analyze_erp_data(
            user_query=user_query,
            intent=intent,
            data=data_list,
            use_deep_analysis=use_deep,
        )

        if raw_data.get("is_stale"):
            content += "\n\n⚠️ Datos servidos desde caché temporal para proteger tu cuota de Bind ERP."

        chart_config = await suggest_chart_config(intent, data_list)
        insight = f"Se analizaron {len(data_list)} registros del módulo {intent.lower()}." if data_list else None

        return {
            "content": content,
            "chartData": data_list,
            "chart_type": chart_config["chart_type"],
            "source": raw_data.get("source", ""),
            "is_stale": raw_data.get("is_stale", False),
            "insight": insight,
        }


# =====================================================================
# AGENT 4: SUPERVISOR AGENT
# Último filtro: zero data leakage hacia el dashboard del cliente
# =====================================================================
class SupervisorAgent:
    FORBIDDEN_TERMS = [
        "api_key", "api key", "internal error", "bind_client", "traceback",
        "python", "dataframe", "sql", "error 429", "raise", "exception",
        "stack trace", "service_role", "supabase_url", "pgcrypto", "jwt",
        "encrypted_token", "tenant_id:", "select *", "insert into",
        "asyncpg", "database_url", "neon",
    ]

    async def validate_response(self, report: dict, trace_id: str = "?") -> dict:
        content = report.get("content", "").lower()

        for term in self.FORBIDDEN_TERMS:
            if term in content:
                logger.warning(f"[Trace {trace_id}] Supervisor: FUGA '{term}' bloqueada.")
                report["content"] = (
                    "Tuve un inconveniente al formatear el reporte, pero tus datos están seguros. "
                    "¿Podrías reformular la pregunta?"
                )
                report["chartData"] = None
                report["insight"] = None
                break

        if isinstance(report.get("chartData"), list) and len(report["chartData"]) == 0:
            report["content"] += "\n\n*(No se encontraron registros en Bind ERP para esta consulta)*"

        return report


# =====================================================================
# ORCHESTRATOR: Router → DataAnalyst → ReportGenerator → Supervisor
# =====================================================================
async def process_user_request(
    user_query: str,
    tenant_id: str,
    bind_client,
    cache,
    trace_id: str,
) -> dict:
    router   = RouterAgent()
    analyst  = DataAnalystAgent(bind_client, cache)
    reporter = ReportGeneratorAgent()
    supervisor = SupervisorAgent()

    logger.info(f"[Trace {trace_id}] Tenant {tenant_id} → '{user_query}'")

    # 1. ROUTER: clasificar intent (keyword → Gemini fallback)
    route_result = await router.route(user_query)
    intent = route_result.get("intent", "AMBIGUOUS")
    logger.info(f"[Trace {trace_id}] Router → {intent}")

    if intent in ["REJECT", "AMBIGUOUS"]:
        safe = await supervisor.validate_response({
            "content": route_result.get("message", "¿Podrías reformular tu pregunta?"),
            "chartData": None,
        }, trace_id)
        status = "REJECTED" if intent == "REJECT" else "AMBIGUOUS"
        return _build_response(trace_id, intent, status, safe)

    # 2. DATA ANALYST: caché o llamada a Bind ERP
    raw_data = await analyst.fetch_data(intent)
    if raw_data.get("status") == "error":
        safe = await supervisor.validate_response({
            "content": raw_data.get("message", "Error al obtener datos."),
            "chartData": None,
        }, trace_id)
        return _build_response(trace_id, intent, "ERROR", safe)

    # 3. REPORT GENERATOR: Gemini analiza + formatea
    report = await reporter.format_for_frontend(raw_data, intent, user_query)

    # 4. SUPERVISOR: filtro de seguridad final
    final = await supervisor.validate_response(report, trace_id)

    status = "DEGRADED_CACHE" if final.get("is_stale") else "SUCCESS"
    return _build_response(trace_id, intent, status, final)


def _build_response(trace_id: str, intent: str, status: str, report: dict) -> dict:
    return {
        "trace_id": trace_id,
        "intent": intent,
        "status": status,
        "response": {
            "content": report.get("content", ""),
            "chartData": report.get("chartData"),
            "chart_type": report.get("chart_type"),
            "insight": report.get("insight"),
        },
        "is_stale": report.get("is_stale", False),
        "source": report.get("source"),
    }
