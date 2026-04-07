"""
Atollom AI — Rate Limiting por Tenant

Protege la cuota diaria de cada empresa:
- MAX_REQUESTS_PER_DAY: Límite total de peticiones al chat por tenant
- MAX_BIND_CALLS_PER_DAY: Límite de llamadas reales a la API de Bind por tenant

Backend:
- Redis: Contadores con TTL de 24h (auto-reset a medianoche UTC)
- In-Memory: Fallback para desarrollo (se resetea al reiniciar)
"""

import time
import logging
from typing import Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger("atollom.ratelimit")


@dataclass
class RateLimitStatus:
    """Resultado de la verificación de rate limit."""
    allowed: bool
    requests_used: int
    requests_limit: int
    bind_calls_used: int
    bind_calls_limit: int
    message: str = ""

    @property
    def requests_remaining(self) -> int:
        return max(0, self.requests_limit - self.requests_used)

    @property
    def bind_calls_remaining(self) -> int:
        return max(0, self.bind_calls_limit - self.bind_calls_used)


class RateLimiter:
    """
    Rate limiter dual (Redis / In-Memory) con contadores diarios por tenant.
    Los contadores se resetean automáticamente cada 24 horas.
    """

    def __init__(self, max_requests: int = 200, max_bind_calls: int = 50):
        self.max_requests = max_requests
        self.max_bind_calls = max_bind_calls
        self._redis = None
        self._memory_counters: Dict[str, Tuple[float, int, int]] = {}  # key -> (day_start, requests, bind_calls)
        self._init_backend()

    def _init_backend(self):
        """Intenta conectar a Redis. Si no, usa contadores en memoria."""
        from config import get_settings
        settings = get_settings()
        try:
            import redis
            self._redis = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
            self._redis.ping()
            logger.info("✅ Rate Limiter conectado a Redis")
        except Exception as e:
            if settings.APP_ENV == "production":
                logger.critical(f"Redis no disponible para Rate Limiting en PRODUCCIÓN ({e}). Deteniendo aplicación.")
                raise RuntimeError(f"Fallo crítico: Redis es obligatorio en producción (Operación Muralla China). Detalles: {e}")
            
            self._redis = None
            logger.warning("⚠️ Rate Limiter usando contadores in-memory (no persistentes)")

    def _get_day_key(self, tenant_id: str, counter_type: str) -> str:
        """Genera key con fecha para auto-expiración diaria."""
        from datetime import datetime, timezone
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"atollom:ratelimit:{tenant_id}:{counter_type}:{today}"

    def check_request_limit(self, tenant_id: str) -> RateLimitStatus:
        """Verifica si el tenant puede hacer más requests al chat."""
        requests_used = self._get_counter(tenant_id, "requests")
        bind_calls_used = self._get_counter(tenant_id, "bind_calls")

        if requests_used >= self.max_requests:
            logger.warning(f"[Tenant {tenant_id}] RATE LIMIT: {requests_used}/{self.max_requests} requests agotados")
            return RateLimitStatus(
                allowed=False,
                requests_used=requests_used,
                requests_limit=self.max_requests,
                bind_calls_used=bind_calls_used,
                bind_calls_limit=self.max_bind_calls,
                message=(
                    "Has alcanzado el límite diario de consultas para tu plan. "
                    "Tu cuota se renueva automáticamente a medianoche UTC. "
                    "Contacta a tu administrador si necesitas un plan superior."
                ),
            )

        return RateLimitStatus(
            allowed=True,
            requests_used=requests_used,
            requests_limit=self.max_requests,
            bind_calls_used=bind_calls_used,
            bind_calls_limit=self.max_bind_calls,
        )

    def check_bind_call_limit(self, tenant_id: str) -> bool:
        """Verifica si el tenant puede hacer más llamadas a Bind ERP."""
        used = self._get_counter(tenant_id, "bind_calls")
        return used < self.max_bind_calls

    def increment_request(self, tenant_id: str) -> int:
        """Incrementa el contador de requests del tenant. Retorna el nuevo total."""
        return self._increment_counter(tenant_id, "requests")

    def increment_bind_call(self, tenant_id: str) -> int:
        """Incrementa el contador de Bind API calls del tenant."""
        return self._increment_counter(tenant_id, "bind_calls")

    def get_usage(self, tenant_id: str) -> Dict[str, int]:
        """Retorna el uso actual del tenant (para dashboards/admin)."""
        return {
            "requests_used": self._get_counter(tenant_id, "requests"),
            "requests_limit": self.max_requests,
            "bind_calls_used": self._get_counter(tenant_id, "bind_calls"),
            "bind_calls_limit": self.max_bind_calls,
        }

    # --- Backend Redis ---
    def _get_counter(self, tenant_id: str, counter_type: str) -> int:
        if self._redis:
            return self._get_counter_redis(tenant_id, counter_type)
        return self._get_counter_memory(tenant_id, counter_type)

    def _increment_counter(self, tenant_id: str, counter_type: str) -> int:
        if self._redis:
            return self._increment_counter_redis(tenant_id, counter_type)
        return self._increment_counter_memory(tenant_id, counter_type)

    def _get_counter_redis(self, tenant_id: str, counter_type: str) -> int:
        key = self._get_day_key(tenant_id, counter_type)
        val = self._redis.get(key)
        return int(val) if val else 0

    def _increment_counter_redis(self, tenant_id: str, counter_type: str) -> int:
        key = self._get_day_key(tenant_id, counter_type)
        pipe = self._redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, 86400)  # Auto-expirar en 24h
        results = pipe.execute()
        return results[0]

    # --- Backend In-Memory ---
    def _get_counter_memory(self, tenant_id: str, counter_type: str) -> int:
        key = f"{tenant_id}:{counter_type}"
        if key in self._memory_counters:
            day_start, requests, bind_calls = self._memory_counters[key]
            # Reset si pasaron 24h
            if time.time() - day_start > 86400:
                del self._memory_counters[key]
                return 0
            return requests if counter_type == "requests" else bind_calls
        return 0

    def _increment_counter_memory(self, tenant_id: str, counter_type: str) -> int:
        key = f"{tenant_id}:{counter_type}"
        if key not in self._memory_counters:
            self._memory_counters[key] = (time.time(), 0, 0)

        day_start, requests, bind_calls = self._memory_counters[key]

        # Reset si pasaron 24h
        if time.time() - day_start > 86400:
            day_start = time.time()
            requests = 0
            bind_calls = 0

        if counter_type == "requests":
            requests += 1
        else:
            bind_calls += 1

        self._memory_counters[key] = (day_start, requests, bind_calls)
        return requests if counter_type == "requests" else bind_calls


def create_rate_limiter() -> RateLimiter:
    """Factory que crea el rate limiter con la configuración actual."""
    from config import get_settings
    settings = get_settings()
    return RateLimiter(
        max_requests=settings.RATE_LIMIT_MAX_REQUESTS_PER_DAY,
        max_bind_calls=settings.RATE_LIMIT_MAX_BIND_CALLS_PER_DAY,
    )


# Instancia global
rate_limiter = create_rate_limiter()
