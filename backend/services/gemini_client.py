"""
Gemini AI Client — Cerebro del Bind RP Agent
Modelos en uso:
  - gemini-2.0-flash  : RPD ilimitado → enrutamiento + resúmenes rápidos
  - gemini-2.5-flash  : 10K RPD → análisis financiero profundo
"""
import json
import logging
from typing import Any, Dict, List, Optional

import google.generativeai as genai
from google.generativeai.types import GenerationConfig

from config import get_settings

logger = logging.getLogger("atollom.gemini")

# ====================================================================
# SYSTEM PROMPT — Contexto de negocio para los 600 tenants
# ====================================================================
SYSTEM_PROMPT = """Eres Atollom AI, un analista financiero y operativo senior especializado en empresas mexicanas que usan Bind ERP.

REGLAS ABSOLUTAS:
1. NUNCA inventes datos. Analiza ÚNICAMENTE los datos que se te proporcionen.
2. Responde siempre en español profesional, conciso y orientado a decisiones de negocio.
3. Usa terminología mexicana: pesos MXN (nunca USD salvo que el dato lo indique), RFC, CFDI, almacén.
4. Si los datos están vacíos o son insuficientes, dilo claramente sin inventar nada.
5. No menciones términos técnicos internos (API keys, SQL, JSON, endpoints, tenant_id).
6. Cuando el usuario pida un comparativo o tendencia, estructura la respuesta con métricas claras.
7. Mantén respuestas entre 3 y 6 oraciones ejecutivas, salvo que se solicite un reporte extenso.
"""

# ====================================================================
# GEMINI CLIENT (Singleton)
# ====================================================================
class GeminiClient:
    _primary: Optional[Any] = None
    _analysis: Optional[Any] = None
    _configured: bool = False

    @classmethod
    def _configure(cls):
        if cls._configured:
            return
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY no configurada. El agente usará respuestas genéricas.")
            return
        genai.configure(api_key=settings.GEMINI_API_KEY)
        cls._configured = True
        logger.info(f"Gemini configurado. Primario: {settings.GEMINI_PRIMARY_MODEL} | Análisis: {settings.GEMINI_ANALYSIS_MODEL}")

    @classmethod
    def get_primary(cls) -> Optional[Any]:
        """gemini-2.0-flash — RPD ilimitado, rápido, para todas las peticiones."""
        if cls._primary is None:
            cls._configure()
            settings = get_settings()
            if cls._configured:
                cls._primary = genai.GenerativeModel(
                    model_name=settings.GEMINI_PRIMARY_MODEL,
                    system_instruction=SYSTEM_PROMPT,
                    generation_config=GenerationConfig(
                        max_output_tokens=settings.GEMINI_MAX_TOKENS,
                        temperature=settings.GEMINI_TEMPERATURE,
                    ),
                )
        return cls._primary

    @classmethod
    def get_analysis(cls) -> Optional[Any]:
        """gemini-2.5-flash — Análisis profundo, para reportes complejos."""
        if cls._analysis is None:
            cls._configure()
            settings = get_settings()
            if cls._configured:
                cls._analysis = genai.GenerativeModel(
                    model_name=settings.GEMINI_ANALYSIS_MODEL,
                    system_instruction=SYSTEM_PROMPT,
                    generation_config=GenerationConfig(
                        max_output_tokens=settings.GEMINI_MAX_TOKENS,
                        temperature=settings.GEMINI_TEMPERATURE,
                    ),
                )
        return cls._analysis


# ====================================================================
# HELPER: Clasificar intent con Gemini (fallback del RouterAgent)
# ====================================================================
async def classify_intent_with_gemini(user_query: str) -> Dict[str, str]:
    """
    Usa Gemini para clasificar intenciones ambiguas que el RouterAgent
    basado en keywords no pudo resolver.
    """
    model = GeminiClient.get_primary()
    if not model:
        return {"intent": "AMBIGUOUS", "message": "No pude clasificar tu solicitud. Por favor, especifica si es sobre Ventas, Inventario, Compras, Contabilidad o Directorio."}

    prompt = f"""Clasifica la siguiente solicitud de un usuario de Bind ERP en UNA sola categoría.

Solicitud: "{user_query}"

Categorías válidas:
- VENTAS: facturas, cobros, clientes, cotizaciones, ingresos, revenue
- INVENTARIO: productos, stock, existencias, almacén, SKU
- COMPRAS: órdenes de compra, proveedores, gastos
- CONTABILIDAD: balance, cuentas, pólizas, fiscal, IVA, ISR
- DIRECTORIO: directorio de clientes o proveedores, contactos, RFC
- REJECT: preguntas no relacionadas con el negocio

Responde ÚNICAMENTE con el JSON: {{"intent": "CATEGORIA", "message": "mensaje si es REJECT o si necesitas más info"}}
Si la categoría es clara, el campo message debe ser null."""

    try:
        response = await model.generate_content_async(prompt)
        text = response.text.strip()
        # Limpiar posible markdown del JSON
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
        return result
    except Exception as e:
        logger.error(f"Gemini classify_intent error: {e}")
        return {"intent": "AMBIGUOUS", "message": "¿Podrías especificar si tu consulta es sobre Ventas, Inventario, Compras, Contabilidad o Directorio?"}


# ====================================================================
# HELPER: Analizar datos de Bind ERP y generar insight ejecutivo
# ====================================================================
async def analyze_erp_data(
    user_query: str,
    intent: str,
    data: List[Any],
    use_deep_analysis: bool = False,
) -> str:
    """
    Convierte datos crudos de Bind ERP en un análisis ejecutivo en español.
    use_deep_analysis=True usa gemini-2.5-flash para análisis más profundo.
    """
    model = GeminiClient.get_analysis() if use_deep_analysis else GeminiClient.get_primary()
    if not model:
        return f"Se encontraron {len(data)} registros en el módulo de {intent.lower()}."

    # Limitar datos enviados a Gemini para optimizar tokens
    sample = data[:30] if len(data) > 30 else data
    omitted = len(data) - len(sample)

    prompt = f"""El usuario preguntó: "{user_query}"
Módulo consultado: {intent}
Total de registros obtenidos de Bind ERP: {len(data)}{f' (mostrando muestra de {len(sample)})' if omitted else ''}

Datos:
{json.dumps(sample, ensure_ascii=False, indent=2, default=str)}

Proporciona un análisis ejecutivo en español que incluya:
1. Respuesta directa a lo que preguntó el usuario
2. La métrica o hallazgo más relevante del negocio
3. Una recomendación o insight accionable (si los datos lo permiten)

Sé conciso. Máximo 5 oraciones. Usa formato de texto limpio sin bullets ni markdown."""

    try:
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini analyze_erp_data error: {e}")
        return f"Se procesaron {len(data)} registros del módulo {intent}. Consulta los datos en la gráfica adjunta."


# ====================================================================
# HELPER: Determinar la mejor representación visual para los datos
# ====================================================================
async def suggest_chart_config(intent: str, data: List[Any]) -> Dict[str, Any]:
    """
    Sugiere el tipo de gráfica más adecuado y el mapeo de campos para Recharts.
    Retorna: {chart_type, x_key, value_key, label}
    """
    # Defaults por módulo sin llamar a Gemini (ahorra RPD)
    defaults = {
        "VENTAS":       {"chart_type": "bar",  "label": "Ventas"},
        "INVENTARIO":   {"chart_type": "pie",  "label": "Inventario"},
        "COMPRAS":      {"chart_type": "line", "label": "Compras"},
        "CONTABILIDAD": {"chart_type": "area", "label": "Contabilidad"},
        "DIRECTORIO":   {"chart_type": "bar",  "label": "Directorio"},
    }
    return defaults.get(intent, {"chart_type": "bar", "label": intent.title()})
