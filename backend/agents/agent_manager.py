from typing import Dict, Any
import logging

logger = logging.getLogger("atollom.agents")

# =====================================================================
# AGENT 1: ROUTER AGENT (FILTRO DE RELEVANCIA Y ENRUTAMIENTO)
# =====================================================================
class RouterAgent:
    """
    System Role: Actúa como el Director de Operaciones (COO) de Atollom AI.
    Tu función es recibir peticiones del usuario y enviarlas al sub-agente especializado.

    Restricciones Críticas:
    - No inventes datos.
    - Clasificación estricta en: VENTAS, INVENTARIO, COMPRAS, CONTABILIDAD, DIRECTORIO.
    - Si la petición no es del ERP: REJECT.
    - Si es ambigua: AMBIGUOUS.
    """

    MODULES = {
        "VENTAS": [
            "venta", "ventas", "factura", "facturas", "facturación", "facturamos",
            "revenue", "ingreso", "ingresos", "vendimos", "cobrar", "cobro",
            "cotización", "cotizaciones", "pedido", "pedidos", "cash flow",
            "cuentas por cobrar", "pago recibido", "pagos recibidos",
        ],
        "INVENTARIO": [
            "inventario", "stock", "existencia", "existencias", "almacén",
            "almacenes", "producto", "productos", "sku", "artículo",
            "rotación", "movimiento", "ajuste", "entrada", "salida",
        ],
        "COMPRAS": [
            "compra", "compras", "proveedor", "proveedores", "orden de compra",
            "cuentas por pagar", "gasto", "gastos", "recepción",
        ],
        "CONTABILIDAD": [
            "contabilidad", "balance", "estado financiero", "póliza", "pólizas",
            "catálogo de cuentas", "asiento contable", "contable", "fiscal",
            "impuesto", "impuestos", "iva", "isr", "cfdi",
        ],
        "DIRECTORIO": [
            "cliente", "clientes", "directorio", "contacto", "contactos",
            "proveedor", "proveedores", "rfc", "razón social",
        ],
    }

    IRRELEVANT_PATTERNS = [
        "chiste", "clima", "cómo estás", "cuento", "quién eres",
        "hola", "adiós", "gracias", "buen día", "buenas tardes",
        "receta", "deporte", "película", "canción", "opinión",
    ]

    def route(self, user_query: str) -> Dict[str, str]:
        query_lower = user_query.lower().strip()

        # Check 1: Filtro de Relevancia (Guardrail contra chistes/charla)
        if any(kw in query_lower for kw in self.IRRELEVANT_PATTERNS):
            return {
                "intent": "REJECT",
                "message": (
                    "Soy Atollom AI, tu asistente de inteligencia financiera y operativa "
                    "conectado a Bind ERP. Puedo ayudarte con consultas sobre Ventas, "
                    "Inventario, Compras, Contabilidad o tu Directorio de clientes. "
                    "¿En qué módulo deseas profundizar?"
                ),
            }

        # Check 2: Clasificación por módulos con detección ampliada
        matched_modules = []
        for module, keywords in self.MODULES.items():
            if any(kw in query_lower for kw in keywords):
                matched_modules.append(module)

        if len(matched_modules) == 1:
            return {"intent": matched_modules[0]}
        elif len(matched_modules) > 1:
            # Si matchea múltiples módulos, priorizar el primero
            return {"intent": matched_modules[0]}

        # Check 3: Petición ambigua pero potencialmente financiera
        financial_clues = ["cuánto", "cuanto", "total", "resumen", "reporte", "métrica",
                          "análisis", "analisis", "comparar", "tendencia", "este mes",
                          "hoy", "semana", "marzo", "febrero", "año"]
        if any(clue in query_lower for clue in financial_clues):
            return {
                "intent": "AMBIGUOUS",
                "message": (
                    "Detecto que deseas información financiera, pero necesito que me "
                    "precises el módulo: ¿Ventas, Inventario, Compras, Contabilidad o Directorio?"
                ),
            }

        return {
            "intent": "AMBIGUOUS",
            "message": (
                "No logré identificar con claridad tu solicitud. ¿Podrías reformularla? "
                "Puedo ayudarte con: Ventas, Inventario, Compras, Contabilidad o Directorio."
            ),
        }


# =====================================================================
# AGENT 2: DATA ANALYST AGENT (EL GUARDIÁN DE BIND Y CACHÉ)
# =====================================================================
class DataAnalystAgent:
    """
    System Role: Eres el Analista de Datos Senior experto en la API de Bind ERP.
    Tu obsesión es la precisión y la eficiencia de costos (Rate Limiting).

    Pensamiento Antes de Actuar (CoT):
    1. ¿El dato está en caché? → Servir sin gastar petición.
    2. ¿El dato es estático o dinámico? → TTL adaptativo.
    3. ¿Quedan peticiones del día? → Bloquearse si no.
    """

    # Mapeo de Intent → método del BindERPClient
    # Verificado contra la API oficial de Bind ERP (developers.bind.com.mx)
    INTENT_TO_ENDPOINT = {
        "VENTAS": "get_invoices",
        "INVENTARIO": "get_inventory",
        "COMPRAS": "get_purchase_orders",
        "CONTABILIDAD": "get_accounts",       # Bind usa /Accounts, no /AccountingJournals
        "DIRECTORIO": "get_clients",
    }

    def __init__(self, bind_client, cache):
        self.bind_client = bind_client
        self.cache = cache
        self.MAX_API_CALLS_PER_QUERY = 2  # Guard estricto contra Alucinación de LLM

    async def fetch_data(self, intent: str, session_calls_count: int = 0) -> Dict[str, Any]:
        if session_calls_count >= self.MAX_API_CALLS_PER_QUERY:
            logger.warning(f"[Tenant {self.bind_client.tenant_id}] Bloqueado: MAX_API_CALLS alcanzado.")
            return {
                "status": "error",
                "message": "Límite de seguridad alcanzado para proteger tu cuota de Bind ERP.",
            }

        cache_key = f"endpoint_{intent}"
        cache_result = self.cache.get(self.bind_client.tenant_id, cache_key)

        # Cache Hit
        if cache_result["data"]:
            source = "Cache (Stale)" if cache_result["is_stale"] else "Cache"
            logger.info(f"[Tenant {self.bind_client.tenant_id}] {source} hit para {intent}")
            return {
                "status": "success",
                "source": source,
                "is_stale": cache_result["is_stale"],
                "data": cache_result["data"],
            }

        # Cache Miss → Llamar a Bind ERP (gasta 1 petición del límite de 20k)
        method_name = self.INTENT_TO_ENDPOINT.get(intent, "get_invoices")
        erp_method = getattr(self.bind_client, method_name, None)

        if erp_method:
            logger.info(f"[Tenant {self.bind_client.tenant_id}] Cache MISS → Llamando {method_name}")
            erp_response = await erp_method()

            # Si Bind retornó un error (ej. 429), intentar Stale Cache como fallback
            if isinstance(erp_response, dict) and erp_response.get("error"):
                logger.error(f"[Tenant {self.bind_client.tenant_id}] Bind error: {erp_response}")
                # Graceful Degradation: si hay Stale data, servirla
                if cache_result["data"]:
                    return {
                        "status": "success",
                        "source": "Cache (Degradado)",
                        "is_stale": True,
                        "data": cache_result["data"],
                    }
                return {
                    "status": "error",
                    "message": erp_response.get("message", "Error al consultar Bind ERP."),
                }

            # Guardar respuesta en Caché inmediatamente
            self.cache.set(self.bind_client.tenant_id, cache_key, erp_response)
            return {
                "status": "success",
                "source": "BindERP_API",
                "is_stale": False,
                "data": erp_response,
            }

        return {"status": "error", "message": f"Módulo '{intent}' no tiene un endpoint configurado."}


# =====================================================================
# AGENT 3: REPORT GENERATOR AGENT (EXPERTO EN UX Y RECHARTS)
# =====================================================================
class ReportGeneratorAgent:
    """
    System Role: Eres un Consultor de Negocios y Experto en UX.
    Transformas datos fríos en insights accionables para la dirección general.
    Seguridad: NUNCA menciones tokens, IDs internos o errores técnicos.
    """

    CHART_TYPE_BY_INTENT = {
        "VENTAS": "bar",
        "INVENTARIO": "pie",
        "COMPRAS": "line",
        "CONTABILIDAD": "area",
        "DIRECTORIO": "bar",
    }

    def format_for_frontend(self, raw_data: Dict[str, Any], intent: str = "VENTAS") -> Dict[str, Any]:
        content = "Aquí tienes los datos solicitados de tu negocio."

        chart_type = self.CHART_TYPE_BY_INTENT.get(intent, "bar")

        if raw_data.get("is_stale"):
            content += (
                "\n\n⚠️ Modo Contingencia: Información servida desde caché temporal "
                "para proteger tu cuota diaria de Bind ERP."
            )

        data_list = raw_data.get("data", [])
        insight = None
        
        # Micro-insight simple: contar los registros de la respuesta
        if data_list and isinstance(data_list, list):
            insight = f"Se encontraron {len(data_list)} registros relevantes para tu empresa."
            
        return {
            "content": content,
            "chartData": data_list,
            "chart_type": chart_type,
            "source": raw_data.get("source", ""),
            "is_stale": raw_data.get("is_stale", False),
            "insight": insight,
        }


# =====================================================================
# AGENT 4: SUPERVISOR AGENT (MIDDLEWARE QA - ZERO DATA LEAKAGE)
# =====================================================================
class SupervisorAgent:
    """
    Actúa como el último filtro de calidad (Quality Assurance).
    Su misión es validar la respuesta y asegurar que NINGÚN dato técnico
    (API keys, SQL, tracebacks, errores de Python) llegue al dashboard del cliente.
    """

    FORBIDDEN_TERMS = [
        "api_key", "api key", "internal error", "bind_client", "traceback",
        "python", "dataframe", "sql", "error 429", "raise", "exception",
        "stack trace", "service_role", "supabase_url", "pgcrypto", "jwt",
        "encrypted_token", "tenant_id:", "select *", "insert into",
    ]

    async def validate_response(self, user_query: str, final_report: dict, trace_id: str = "Unknown") -> dict:
        content = final_report.get("content", "").lower()

        for term in self.FORBIDDEN_TERMS:
            if term in content:
                logger.warning(f"[Trace {trace_id}] Supervisor: FUGA DETECTADA — Término '{term}' bloqueado.")
                final_report["content"] = (
                    "Tuve un inconveniente al procesar el formato del reporte, "
                    "pero tus datos permanecen seguros. ¿Podrías intentar reformular la petición?"
                )
                final_report["chartData"] = None
                final_report["insight"] = None
                break
                
        # Validación de datos vacíos: Si la API no devolvió errores, pero la lista está vacía
        if "chartData" in final_report and isinstance(final_report["chartData"], list) and len(final_report["chartData"]) == 0:
            logger.info(f"[Trace {trace_id}] Supervisor: Datos vacíos detectados, ajustando UX.")
            final_report["content"] += "\n\n*(Nota: No se encontraron registros disponibles en Bind ERP para esta consulta)*"

        return final_report


# =====================================================================
# MAIN PIPELINE ORCHESTRATOR
# =====================================================================
async def process_user_request(
    user_query: str, tenant_id: str, bind_client, cache, trace_id: str
) -> dict:
    """
    Función maestra que orquesta los 4 Agentes de forma lineal y blindada.
    Router → DataAnalyst → ReportGenerator → Supervisor
    """
    router = RouterAgent()
    analyst = DataAnalystAgent(bind_client, cache)
    report_gen = ReportGeneratorAgent()
    supervisor = SupervisorAgent()

    logger.info(f"[Trace {trace_id}] Tenant {tenant_id} - Iniciando pipeline para: '{user_query}'")

    # 1. ROUTER: Clasifica la intención y bloquea peticiones irrelevantes
    route_result = router.route(user_query)
    intent = route_result.get("intent", "AMBIGUOUS")
    logger.info(f"[Trace {trace_id}] Router → {intent}")

    if intent in ["REJECT", "AMBIGUOUS"]:
        safe_report = await supervisor.validate_response(user_query, {
            "content": route_result["message"],
            "chartData": None,
        }, trace_id)
        status = "REJECTED" if intent == "REJECT" else "AMBIGUOUS"
        return _build_response(trace_id, intent, status, safe_report)

    # 2. DATA ANALYST: Busca en caché o ejecuta llamada real (max 2 intentos)
    raw_data = await analyst.fetch_data(intent)
    if raw_data.get("status") == "error":
        safe_report = await supervisor.validate_response(user_query, {
            "content": raw_data.get("message", "Error al obtener datos."),
            "chartData": None,
        }, trace_id)
        return _build_response(trace_id, intent, "ERROR", safe_report)

    # 3. REPORT GENERATOR: Crea visual y texto ejecutivo
    report = report_gen.format_for_frontend(raw_data, intent)

    # 4. SUPERVISOR: Filtro final de seguridad antes del dashboard
    final_output = await supervisor.validate_response(user_query, report, trace_id)

    status = "DEGRADED_CACHE" if final_output.get("is_stale") else "SUCCESS"
    return _build_response(trace_id, intent, status, final_output)


def _build_response(trace_id: str, intent: str, status: str, final_report: dict) -> dict:
    """Construye el dict compatible con el schema ChatResponse."""
    return {
        "trace_id": trace_id,
        "intent": intent,
        "status": status,
        "response": {
            "content": final_report.get("content", ""),
            "chartData": final_report.get("chartData"),
            "chart_type": final_report.get("chart_type"),
            "insight": final_report.get("insight")
        },
        "is_stale": final_report.get("is_stale", False),
        "source": final_report.get("source"),
    }
