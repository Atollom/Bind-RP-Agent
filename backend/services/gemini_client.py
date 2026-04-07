"""
Gemini AI Client — Bind RP Agent
SDK: google-genai (nuevo, reemplaza google-generativeai deprecado)

Modelos:
  gemini-2.0-flash  → RPD ilimitado, análisis rápido (todas las peticiones)
  gemini-2.5-flash  → 10K RPD, análisis profundo (comparativos, tendencias)
"""
import json
import logging
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from config import get_settings

logger = logging.getLogger("atollom.gemini")

SYSTEM_PROMPT = """Eres Atollom AI, analista financiero y operativo senior para empresas mexicanas que usan Bind ERP.

REGLAS:
1. NUNCA inventes datos. Analiza SOLO los datos proporcionados.
2. Responde siempre en español profesional, conciso, orientado a decisiones de negocio.
3. Usa terminología mexicana: pesos MXN, RFC, CFDI, almacén.
4. Si los datos son insuficientes, dilo claramente sin inventar nada.
5. No menciones términos técnicos internos (API, SQL, JSON, tenant_id, endpoint).
6. Para comparativos y tendencias, usa métricas claras y concretas.
7. Máximo 5 oraciones ejecutivas salvo que se pida reporte extenso."""

# ====================================================================
# CLIENTE SINGLETON
# ====================================================================
_client: Optional[genai.Client] = None


def _get_client() -> Optional[genai.Client]:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY no configurada.")
            return None
        _client = genai.Client(api_key=settings.GEMINI_API_KEY)
        logger.info(f"Gemini client iniciado. Primario: {settings.GEMINI_PRIMARY_MODEL}")
    return _client


def _get_config(max_tokens: Optional[int] = None) -> types.GenerateContentConfig:
    settings = get_settings()
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=max_tokens or settings.GEMINI_MAX_TOKENS,
        temperature=settings.GEMINI_TEMPERATURE,
    )


# ====================================================================
# CLASIFICAR INTENT (fallback del RouterAgent)
# ====================================================================
async def classify_intent_with_gemini(user_query: str) -> Dict[str, str]:
    client = _get_client()
    if not client:
        return {"intent": "AMBIGUOUS", "message": "¿Tu consulta es sobre Ventas, Inventario, Compras, Contabilidad o Directorio?"}

    settings = get_settings()
    prompt = f"""Clasifica la solicitud de un usuario de Bind ERP en UNA categoría.

Solicitud: "{user_query}"

Categorías: VENTAS | INVENTARIO | COMPRAS | CONTABILIDAD | DIRECTORIO | REJECT

Responde SOLO con JSON: {{"intent": "CATEGORIA", "message": null}}
Si es REJECT, agrega un mensaje explicando que solo puedes responder sobre el ERP."""

    try:
        response = await client.aio.models.generate_content(
            model=settings.GEMINI_PRIMARY_MODEL,
            contents=prompt,
            config=_get_config(max_tokens=150),
        )
        text = response.text.strip().strip("```json").strip("```").strip()
        return json.loads(text)
    except Exception as e:
        logger.error(f"classify_intent error: {e}")
        return {"intent": "AMBIGUOUS", "message": "¿Sobre qué módulo es tu consulta: Ventas, Inventario, Compras, Contabilidad o Directorio?"}


# ====================================================================
# ANALIZAR DATOS DE BIND ERP → INSIGHT EJECUTIVO
# ====================================================================
async def analyze_erp_data(
    user_query: str,
    intent: str,
    data: List[Any],
    use_deep_analysis: bool = False,
) -> str:
    client = _get_client()
    if not client:
        return f"Se encontraron {len(data)} registros en el módulo de {intent.lower()}."

    settings = get_settings()
    model = settings.GEMINI_ANALYSIS_MODEL if use_deep_analysis else settings.GEMINI_PRIMARY_MODEL

    sample = data[:25] if len(data) > 25 else data
    omitted = len(data) - len(sample)

    prompt = f"""El usuario preguntó: "{user_query}"
Módulo: {intent} | Registros totales: {len(data)}{f' (muestra: {len(sample)})' if omitted else ''}

Datos de Bind ERP:
{json.dumps(sample, ensure_ascii=False, default=str)}

Proporciona un análisis ejecutivo en español:
1. Respuesta directa a la pregunta del usuario
2. El hallazgo más relevante del negocio
3. Una recomendación accionable (si los datos lo permiten)

Máximo 5 oraciones. Texto limpio, sin bullets ni markdown."""

    try:
        response = await client.aio.models.generate_content(
            model=model,
            contents=prompt,
            config=_get_config(),
        )
        return response.text.strip()
    except Exception as e:
        logger.error(f"analyze_erp_data error: {e}")
        return f"Se procesaron {len(data)} registros del módulo {intent}. Consulta la gráfica adjunta para más detalles."


# ====================================================================
# CONFIGURACIÓN DE GRÁFICA (sin LLM — ahorra RPD)
# ====================================================================
def suggest_chart_config(intent: str) -> Dict[str, str]:
    defaults = {
        "VENTAS":       {"chart_type": "bar",  "label": "Ventas"},
        "INVENTARIO":   {"chart_type": "pie",  "label": "Inventario"},
        "COMPRAS":      {"chart_type": "line", "label": "Compras"},
        "CONTABILIDAD": {"chart_type": "area", "label": "Contabilidad"},
        "DIRECTORIO":   {"chart_type": "bar",  "label": "Directorio"},
    }
    return defaults.get(intent, {"chart_type": "bar", "label": intent.title()})
