---
name: Bind ERP API Integration Rules
description: Arquitectura de integración y gestión de límites para la API de Bind ERP.
---

# Contexto de la Integración (Bind ERP API)

## Autenticación
- **Método:** Las peticiones deben usar `Bearer Token` en la cabecera (header) de autorización: `Authorization: Bearer <token>`.
- El token debe obtenerse de manera segura desde el esquema de base de datos cifrado de cada cliente en Supabase, nunca desde el cliente de Next.js.

## Gestión de Límites de Peticiones (Rate Limiting)
- **Límite Estricto:** Existe un límite riguroso de 20,000 peticiones diarias por cliente (tenant).
- **Estrategia de Caché Obligatoria:** El backend construido en FastAPI DEBE implementar una capa de caché robusta (utilizando Redis o memoria estructurada persistente).
- **Regla de Ejecución:** El agente `DataAnalyst` debe consultar siempre el caché antes de invocar cualquier petición hacia la API de Bind. Solo en caso de *Cache Miss* se permite gastar una petición del límite diario.

## Mapeo de Módulos (Bind ERP)
La API del ERP está dividida estructuralmente en 5 áreas clave. Las llamadas hacia el API deben agruparse bajo la estructura correspondiente:
1. **Ventas y Facturación:** Rutas relacionadas (ej. `/api/Invoices`), gestión de clientes de venta, oportunidades, cotizaciones.
2. **Inventarios y Almacenes:** Rutas de existencia (ej. `/api/Inventory`), control de stock, movimientos, ajustes, líneas de productos.
3. **Compras:** Manejo de órdenes de compra, recepciones, proveedores.
4. **Contabilidad:** Balances, movimientos contables, pólizas y cuentas de catálogo.
5. **Directorio:** Gestión completa y directorio general de Clientes y Proveedores.
