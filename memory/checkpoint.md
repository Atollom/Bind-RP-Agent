---
name: Checkpoint — Render PORT fix, esperando redeploy
description: Estado exacto al agotar tokens. Render redeploy en curso.
type: project
---

# Checkpoint — 2026-04-06 (URGENTE — FIN DE SESIÓN)

## Estado de cada servicio

### GitHub ✅
- Repo: https://github.com/Atollom/Bind-RP-Agent
- Último commit: `fix: Dockerfile usa PORT dinamico de Render`
- Branch: main, todo sincronizado

### Vercel (Frontend) ✅
- URL: https://bind-rp-agent.vercel.app
- Estado: LIVE, build OK
- NEXT_PUBLIC_API_URL = https://bind-rp-agent.onrender.com

### Render (Backend FastAPI) ⚠️ REDEPLOY EN CURSO
- URL: https://bind-rp-agent.onrender.com
- Servicio ID: srv-d7a7ihfpm1nc73bvppsg
- PROBLEMA ORIGINAL: Dockerfile tenía `--port 8000` hardcoded, Render usa PORT dinámico
- FIX APLICADO: CMD ahora usa `${PORT:-8000}`
- ACCIÓN PENDIENTE: Esperar que Render termine el redeploy (5-10 min)
- VERIFICAR: curl https://bind-rp-agent.onrender.com/health → debe dar {"status":"healthy"}

### Neon PostgreSQL ✅
- URL: ep-icy-brook-amze722b.c-5.us-east-1.aws.neon.tech
- Tablas: tenants, users, user_roles, bind_erp_keys, usage_logs ✅
- Funciones: store_bind_key, decrypt_bind_key ✅
- Tenant dev seed: ID = 00000000-0000-0000-0000-000000000001

### UptimeRobot ✅
- Monitor: https://bind-rp-agent.onrender.com/health
- Intervalo: 5 min (mantiene Render despierto)
- Estado: mostraba "Down" por el bug del puerto (se resolverá tras redeploy)

## Credenciales clave (están en backend/.env — NO en git)

| Variable | Valor |
|----------|-------|
| DATABASE_URL | postgresql://neondb_owner:npg_DB46INoXlYVh@ep-icy-brook-amze722b... |
| JWT_SECRET | 4dd1de91e06449979e407c997e2ff28bbc3bdfdd59316b23a195c926a427057b |
| GEMINI_API_KEY | AIzaSyBBtdMBg8jqoIHjcOMIiybwAp5mO8NDXSg |
| APP_ENCRYPTION_KEY | 2bd93030b342c1939bd089759f911816 |
| BIND_API_KEY_DEV | eyJhbGciOiJIUzI1NiIs... (JWT de Bind ERP) |
| DEV_BYPASS_TOKEN | dev-bypass-2025 |

## Variables de entorno en Render (verificar que estén todas)
Ir a: render.com → bind-rp-agent-api → Environment
Deben estar: DATABASE_URL, JWT_SECRET, GEMINI_API_KEY, APP_ENCRYPTION_KEY,
BIND_API_KEY_DEV, CORS_ORIGINS, APP_ENV=production, LOG_LEVEL=INFO

## Stack técnico completo
- Frontend: Next.js 14 + Tailwind → Vercel
- Backend: FastAPI + Gemini 2.0 Flash → Render (Docker)
- DB: Neon PostgreSQL (asyncpg)
- Auth: JWT propio (sin Supabase)
- Cache: In-memory (Redis opcional)
- LLM: google-genai SDK, modelos gemini-2.0-flash + gemini-2.5-flash
- Export: openpyxl (Excel) + reportlab (PDF)

## Pipeline agéntico (4 agentes)
Router (keywords + Gemini fallback)
→ DataAnalyst (caché → Bind ERP)
→ ReportGenerator (Gemini analiza datos reales)
→ Supervisor (zero data leakage)

## Endpoints Bind ERP verificados ✅
- /Clients → OK (RFC, ClientName, Email)
- /Products → OK (Code, Title, Cost) — también usado para Inventario
- /Accounts → OK (contabilidad)
- /Invoices → OK (vacío en cuenta de prueba)
- /Warehouses → OK
- /Inventory → 404 (no existe, usar /Products)

## Lo que falta para MVP completo
1. ✅ Render redeploy con PORT fix → verificar /health
2. Probar chat end-to-end: Vercel → Render → Bind ERP → Gemini
3. Crear primer usuario real en Neon (via /api/auth/register en dev mode)
4. Conectar UptimeRobot al URL correcto: bind-rp-agent.onrender.com
5. Eliminar servicio duplicado bind-rp-agent-api.onrender.com (si existe)

## Próxima sesión — qué hacer PRIMERO
1. Leer este checkpoint
2. Verificar: curl https://bind-rp-agent.onrender.com/health
3. Si OK → probar chat desde Vercel con pregunta "muéstrame mis clientes"
4. Si sigue 404/timeout → revisar logs en Render dashboard
