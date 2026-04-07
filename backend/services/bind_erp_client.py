import httpx
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger("atollom.bind")


class BindERPClient:
    """
    Cliente asíncrono para comunicarse con la API de Bind ERP.
    Referencia oficial: https://developers.bind.com.mx

    Autenticación: Authorization: Bearer <API_KEY>
    Base URL: https://api.bind.com.mx/api
    Filtros soportados: OData ($filter, $top, $skip)

    Incluye: manejo de errores HTTP, connection pooling, paginación OData.
    """
    BASE_URL = "https://api.bind.com.mx/api"

    # Límite de registros por página de la API de Bind
    DEFAULT_PAGE_SIZE = 50

    def __init__(self, tenant_id: str, api_key: str):
        self.tenant_id = tenant_id
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Connection pooling: reutilizar conexiones para eficiencia
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.BASE_URL,
                headers=self.headers,
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Any:
        client = await self._get_client()

        try:
            response = await client.request(method, endpoint, params=params, json=data)

            # Manejo de errores HTTP específicos de Bind
            if response.status_code == 401:
                logger.error(f"[Tenant {self.tenant_id}] API Key inválida o expirada (401).")
                return {"error": True, "code": 401, "message": "API Key de Bind ERP inválida o expirada. Contacta a tu administrador."}

            if response.status_code == 404:
                logger.warning(f"[Tenant {self.tenant_id}] Recurso no encontrado (404): {endpoint}")
                return {"error": True, "code": 404, "message": f"El recurso '{endpoint}' no fue encontrado en Bind ERP."}

            if response.status_code == 429:
                logger.critical(f"[Tenant {self.tenant_id}] LÍMITE DE PETICIONES ALCANZADO (429).")
                return {"error": True, "code": 429, "message": "Se alcanzó el límite diario de Bind ERP (10,000 peticiones). Intenta mañana."}

            if response.status_code >= 500:
                logger.error(f"[Tenant {self.tenant_id}] Error interno de Bind ERP ({response.status_code}).")
                return {"error": True, "code": response.status_code, "message": "Bind ERP no está respondiendo. Intenta en unos minutos."}

            response.raise_for_status()
            body = response.json()

            # Bind ERP envuelve los registros en {"value": [...], "nextLink": "...", "count": N}
            # Extraemos el array directamente para normalizar la respuesta
            if isinstance(body, dict) and "value" in body:
                return body["value"]
            return body

        except httpx.TimeoutException:
            logger.error(f"[Tenant {self.tenant_id}] Timeout al consultar {endpoint}")
            return {"error": True, "code": 408, "message": "La consulta a Bind ERP tomó demasiado tiempo. Intenta nuevamente."}
        except httpx.ConnectError:
            logger.error(f"[Tenant {self.tenant_id}] No se pudo conectar a Bind ERP")
            return {"error": True, "code": 503, "message": "No se pudo conectar con Bind ERP. Verifica tu conexión a internet."}

    # =========================================================
    # HELPERS: Filtros OData para paginación y búsqueda
    # =========================================================
    def _build_odata_params(
        self,
        params: Optional[Dict] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None,
        odata_filter: Optional[str] = None,
    ) -> Dict:
        """
        Construye parámetros OData compatibles con la API de Bind ERP.
        - $top: límite de registros (paginación)
        - $skip: offset (paginación)
        - $filter: filtro OData (ej. "Date ge 2024-01-01")
        """
        merged = dict(params or {})
        if top is not None:
            merged["$top"] = top
        if skip is not None:
            merged["$skip"] = skip
        if odata_filter:
            merged["$filter"] = odata_filter
        return merged

    # =========================================================
    # Módulo 1: VENTAS Y FACTURACIÓN
    # Endpoints verificados: /Invoices, /Quotes, /Payments
    # =========================================================
    async def get_invoices(self, params: Optional[Dict] = None, top: int = 50, skip: int = 0) -> Any:
        """Obtener lista de ventas/facturas. Soporta paginación OData."""
        return await self._request("GET", "/Invoices", params=self._build_odata_params(params, top, skip))

    async def get_invoice_detail(self, invoice_id: str) -> Any:
        """Obtener detalle de una factura específica."""
        return await self._request("GET", f"/Invoices/{invoice_id}")

    async def get_quotes(self, params: Optional[Dict] = None) -> Any:
        """Obtener cotizaciones."""
        return await self._request("GET", "/Quotes", params=params)

    async def get_payments(self, params: Optional[Dict] = None) -> Any:
        """Obtener pagos recibidos."""
        return await self._request("GET", "/Payments", params=params)

    # =========================================================
    # Módulo 2: INVENTARIOS Y ALMACENES
    # Endpoints verificados: /Inventory, /Products, /Warehouses
    # =========================================================
    async def get_inventory(self, params: Optional[Dict] = None) -> Any:
        """Obtener niveles de stock actuales. Filtrable por almacén."""
        return await self._request("GET", "/Inventory", params=params)

    async def get_products(self, params: Optional[Dict] = None, top: int = 50, skip: int = 0) -> Any:
        """Obtener lista de productos y servicios."""
        return await self._request("GET", "/Products", params=self._build_odata_params(params, top, skip))

    async def get_product_detail(self, product_id: str) -> Any:
        """Obtener detalle de un producto específico."""
        return await self._request("GET", f"/Products/{product_id}")

    async def get_warehouses(self, params: Optional[Dict] = None) -> Any:
        """Obtener lista de almacenes."""
        return await self._request("GET", "/Warehouses", params=params)

    # =========================================================
    # Módulo 3: COMPRAS
    # Endpoints verificados: /Orders, /Providers
    # =========================================================
    async def get_purchase_orders(self, params: Optional[Dict] = None, top: int = 50, skip: int = 0) -> Any:
        """Obtener órdenes de compra."""
        return await self._request("GET", "/Orders", params=self._build_odata_params(params, top, skip))

    async def get_order_detail(self, order_id: str) -> Any:
        """Obtener detalle de una orden de compra."""
        return await self._request("GET", f"/Orders/{order_id}")

    # =========================================================
    # Módulo 4: CONTABILIDAD
    # Endpoints verificados: /Accounts
    # Nota: Bind NO tiene un endpoint /AccountingJournals público.
    # Se usa /Accounts (catálogo de cuentas contables).
    # =========================================================
    async def get_accounts(self, params: Optional[Dict] = None) -> Any:
        """Obtener catálogo de cuentas contables."""
        return await self._request("GET", "/Accounts", params=params)

    # =========================================================
    # Módulo 5: DIRECTORIO (Clientes y Proveedores)
    # Endpoints verificados: /Clients, /Providers
    # =========================================================
    async def get_clients(self, params: Optional[Dict] = None, top: int = 50, skip: int = 0) -> Any:
        """Obtener lista de clientes."""
        return await self._request("GET", "/Clients", params=self._build_odata_params(params, top, skip))

    async def get_client_detail(self, client_id: str) -> Any:
        """Obtener detalle de un cliente."""
        return await self._request("GET", f"/Clients/{client_id}")

    async def get_providers(self, params: Optional[Dict] = None, top: int = 50, skip: int = 0) -> Any:
        """Obtener lista de proveedores."""
        return await self._request("GET", "/Providers", params=self._build_odata_params(params, top, skip))

    async def get_provider_detail(self, provider_id: str) -> Any:
        """Obtener detalle de un proveedor."""
        return await self._request("GET", f"/Providers/{provider_id}")

    # =========================================================
    # Módulo 6: CATÁLOGOS Y RECURSOS DEL SISTEMA
    # Endpoints verificados: /Banks, /Currencies, /PriceLists, /Users
    # =========================================================
    async def get_banks(self, params: Optional[Dict] = None) -> Any:
        """Obtener lista de bancos disponibles."""
        return await self._request("GET", "/Banks", params=params)

    async def get_currencies(self, params: Optional[Dict] = None) -> Any:
        """Obtener monedas soportadas."""
        return await self._request("GET", "/Currencies", params=params)

    async def get_price_lists(self, params: Optional[Dict] = None) -> Any:
        """Obtener listas de precios."""
        return await self._request("GET", "/PriceLists", params=params)
