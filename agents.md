# Atollom AI - Agent Architecture

Este documento define la estructura del sistema agéntico para interactuar con el backend y procesar las peticiones del usuario hacia la API de Bind ERP.

## Roles del Equipo

### 1. Router (Enrutador)
**Responsabilidad:** Clasificar la intención del usuario. Analiza la petición original y determina a qué agente o flujo de trabajo debe dirigirse la solicitud.
**Reglas:**
- No ejecuta consultas a bases de datos ni a la API externa.
- Evalúa el contexto y delega la tarea al sub-agente adecuado (ej., peticiones de análisis de ventas, consultas de stock, reportes financieros).

### 2. DataAnalyst (Analista de Datos)
**Responsabilidad:** Es el único rol autorizado para hacer peticiones en Python a la API de Bind ERP a través de nuestro Backend en FastAPI.
**Reglas:**
- Gestiona la conexión con FastAPI para obtener la información solicitada.
- Debe tener en cuenta estrictamente los límites de la API de Bind (20,000 peticiones/día) y consultar el caché (Redis o interno) antes de realizar una petición externa.
- Convierte los datos crudos del JSON de la API en estructuras de datos procesables para el backend.

### 3. ReportGenerator (Generador de Reportes)
**Responsabilidad:** Formatear la respuesta procesada por el DataAnalyst y prepararla para ser enviada al frontend (Dashboard Web/Móvil con chat).
**Reglas:**
- Diseña y estructura las respuestas considerando componentes visuales de Next.js (Recharts, tablas de datos).
- Utiliza un lenguaje profesional y estructurado que aporte valor empresarial.
- Nunca expone datos confidenciales, tokens ni estructuras internas del sistema al usuario final.
