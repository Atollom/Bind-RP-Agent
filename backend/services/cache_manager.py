"""
Atollom AI — Sistema de Caché Dual (Redis + In-Memory Fallback)

Arquitectura:
- PRODUCCIÓN: Redis persistente → sobrevive reinicios de Docker/servidor
- DESARROLLO: In-Memory automático si Redis no está disponible
- DEGRADACIÓN: Si Redis cae en producción, el sistema sigue operando con in-memory

Política de TTL:
- Dato Fresco: CACHE_TTL_SECONDS (default 5 min)
- Modo Contingencia: CACHE_GRACE_PERIOD_SECONDS (default 24h) — Graceful Degradation
"""

import time
import json
import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger("atollom.cache")


# =====================================================================
# INTERFAZ BASE
# =====================================================================
class BaseCacheManager(ABC):
    """Contrato que deben cumplir todas las implementaciones de caché."""

    @abstractmethod
    def get(self, tenant_id: str, endpoint: str, query_params: str = "") -> Dict[str, Any]:
        """Retorna {'data': Any | None, 'is_stale': bool}"""
        ...

    @abstractmethod
    def set(self, tenant_id: str, endpoint: str, data: Any, query_params: str = "") -> None:
        ...

    @abstractmethod
    def delete(self, tenant_id: str, endpoint: str, query_params: str = "") -> None:
        ...

    @abstractmethod
    def flush_tenant(self, tenant_id: str) -> int:
        """Elimina todo el caché de un tenant. Retorna cantidad de keys eliminadas."""
        ...

    def _generate_key(self, tenant_id: str, endpoint: str, query_params: str) -> str:
        return f"atollom:cache:{tenant_id}:{endpoint}:{query_params}"


# =====================================================================
# IMPLEMENTACIÓN REDIS (PRODUCCIÓN)
# =====================================================================
class RedisCacheManager(BaseCacheManager):
    """Caché persistente con Redis — sobrevive reinicios del servidor."""

    def __init__(self, redis_url: str, ttl: int = 300, grace_period: int = 86400):
        import redis
        self.redis = redis.Redis.from_url(redis_url, decode_responses=True)
        self.TTL_SECONDS = ttl
        self.GRACE_PERIOD_SECONDS = grace_period
        logger.info(f"✅ Redis Cache conectado: {redis_url.split('@')[-1] if '@' in redis_url else redis_url}")

    def get(self, tenant_id: str, endpoint: str, query_params: str = "") -> Dict[str, Any]:
        key = self._generate_key(tenant_id, endpoint, query_params)

        raw = self.redis.get(key)
        if raw is None:
            return {"data": None, "is_stale": False}

        try:
            entry = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            self.redis.delete(key)
            return {"data": None, "is_stale": False}

        created_at = entry.get("created_at", 0)
        age = time.time() - created_at

        # Dato fresco
        if age <= self.TTL_SECONDS:
            return {"data": entry["data"], "is_stale": False}

        # Dato en período de gracia (Graceful Degradation)
        if age <= self.TTL_SECONDS + self.GRACE_PERIOD_SECONDS:
            return {"data": entry["data"], "is_stale": True}

        # Expirado totalmente
        self.redis.delete(key)
        return {"data": None, "is_stale": False}

    def set(self, tenant_id: str, endpoint: str, data: Any, query_params: str = "") -> None:
        key = self._generate_key(tenant_id, endpoint, query_params)
        entry = {
            "created_at": time.time(),
            "data": data,
        }
        # TTL total en Redis = TTL fresco + período de gracia
        total_ttl = self.TTL_SECONDS + self.GRACE_PERIOD_SECONDS
        self.redis.setex(key, total_ttl, json.dumps(entry, default=str))

    def delete(self, tenant_id: str, endpoint: str, query_params: str = "") -> None:
        key = self._generate_key(tenant_id, endpoint, query_params)
        self.redis.delete(key)

    def flush_tenant(self, tenant_id: str) -> int:
        pattern = f"atollom:cache:{tenant_id}:*"
        keys = list(self.redis.scan_iter(match=pattern, count=100))
        if keys:
            return self.redis.delete(*keys)
        return 0


# =====================================================================
# IMPLEMENTACIÓN IN-MEMORY (FALLBACK DE DESARROLLO)
# =====================================================================
class InMemoryCacheManager(BaseCacheManager):
    """Caché en memoria — se borra al reiniciar. Solo para desarrollo."""

    def __init__(self, ttl: int = 300, grace_period: int = 86400):
        self.cache: Dict[str, tuple[float, Any]] = {}
        self.TTL_SECONDS = ttl
        self.GRACE_PERIOD_SECONDS = grace_period
        logger.warning("⚠️ Usando caché IN-MEMORY (no persistente). Solo para desarrollo.")

    def get(self, tenant_id: str, endpoint: str, query_params: str = "") -> Dict[str, Any]:
        key = self._generate_key(tenant_id, endpoint, query_params)

        if key in self.cache:
            created_at, data = self.cache[key]
            age = time.time() - created_at

            if age <= self.TTL_SECONDS:
                return {"data": data, "is_stale": False}
            elif age <= self.TTL_SECONDS + self.GRACE_PERIOD_SECONDS:
                return {"data": data, "is_stale": True}
            else:
                del self.cache[key]

        return {"data": None, "is_stale": False}

    def set(self, tenant_id: str, endpoint: str, data: Any, query_params: str = "") -> None:
        key = self._generate_key(tenant_id, endpoint, query_params)
        self.cache[key] = (time.time(), data)

    def delete(self, tenant_id: str, endpoint: str, query_params: str = "") -> None:
        key = self._generate_key(tenant_id, endpoint, query_params)
        self.cache.pop(key, None)

    def flush_tenant(self, tenant_id: str) -> int:
        prefix = f"atollom:cache:{tenant_id}:"
        keys_to_delete = [k for k in self.cache if k.startswith(prefix)]
        for k in keys_to_delete:
            del self.cache[k]
        return len(keys_to_delete)


# =====================================================================
# FACTORY — Selección automática de backend de caché
# =====================================================================
def create_cache_manager() -> BaseCacheManager:
    """
    Intenta conectar a Redis. Si falla, usa in-memory como fallback.
    Esto permite desarrollo sin Docker/Redis y producción con Redis.
    """
    from config import get_settings
    settings = get_settings()

    try:
        manager = RedisCacheManager(
            redis_url=settings.REDIS_URL,
            ttl=settings.CACHE_TTL_SECONDS,
            grace_period=settings.CACHE_GRACE_PERIOD_SECONDS,
        )
        # Verificar conexión real
        manager.redis.ping()
        return manager
    except Exception as e:
        if settings.APP_ENV == "production":
            logger.critical(f"Redis no disponible en PRODUCCIÓN ({e}). No se permite fallback in-memory. Deteniendo aplicación.")
            raise RuntimeError(f"Fallo crítico: Redis es obligatorio en producción (Operación Muralla China). Detalles: {e}")

        logger.warning(f"Redis no disponible ({e}). Fallback a caché in-memory.")
        return InMemoryCacheManager(
            ttl=settings.CACHE_TTL_SECONDS,
            grace_period=settings.CACHE_GRACE_PERIOD_SECONDS,
        )


# Instancia global — se inicializa al importar
cache_manager = create_cache_manager()
