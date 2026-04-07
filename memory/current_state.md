---
name: Current Project State
description: Estado actual del proyecto Atollom AI — features, archivos, paleta
type: project
---

# Atollom AI — Estado Actual (2026-04-06)

## Stack
- **Frontend:** Next.js 14 + TypeScript + Tailwind CSS + Recharts
- **Backend:** FastAPI (Python) + httpx async
- **Auth:** Supabase (en DEMO MODE actualmente)
- **Cache:** In-memory (Redis opcional, no configurado en dev)
- **Deploy target:** Vercel (frontend) + servidor Python (backend)

## Paleta de Colores
- Background: `#001C3E` (Deep Navy Blue)
- Accent: `#A4DA30` (Electric Lime Green — tailwind: `accent`)
- Text: `#D0DCE3` (tailwind: `textPrimary`)
- Panel: `#002855` (tailwind: `panel`)

## Archivos Clave
### Frontend (`frontend/`)
- `app/page.tsx` — SPA principal con routing por sección (dashboard/chat/módulos)
- `app/globals.css` — Tailwind + glassmorphism + scrollbar custom
- `tailwind.config.ts` — Colores custom: background, accent, textPrimary, panel
- `components/ChatDashboard.tsx` — Chat UI completo con localStorage persistence
- `components/Sidebar.tsx` — Navegación lateral
- `components/KPICards.tsx` — KPIs hardcoded (mock data, pendiente conectar)
- `components/MultiChartVisualizer.tsx` — Recharts (bar/area/pie/line)
- `components/AuthProvider.tsx` — **⚠️ EN DEMO MODE** (access_token = "demo-token")
- `components/AtollomLogo.tsx` — Logo SVG con glow
- `.env.local.example` — Template de env vars frontend

### Backend (`backend/`)
- `main.py` — FastAPI app, CORS, health endpoint
- `config.py` — Settings via pydantic-settings, lee `.env`
- `routers/chat.py` — Endpoint POST /api/chat (pipeline completo)
- `middleware/auth.py` — JWT validation via Supabase secret
- `agents/agent_manager.py` — 4 agentes: Router, DataAnalyst, ReportGenerator, Supervisor
- `services/bind_erp_client.py` — Cliente httpx para Bind ERP (todos los módulos)
- `services/cache_manager.py` — TTL cache (5min fresco / 24h stale)
- `services/rate_limiter.py` — Rate limit: 200 req/día tenant, 50 Bind calls/día
- `services/supabase_client.py` — Admin client Supabase
- `.env.example` — Template de env vars backend (**no existe `.env` real aún**)

### Supabase (`supabase/migrations/`)
- `00001_initial_schema.sql` — tenants, user_roles, etc.
- `00002_vault_and_keys.sql` — schema privado para API keys cifradas (pgcrypto)
- `00003_usage_logs.sql` — tabla usage_logs
- `00004_complete_rls_policies.sql` — RLS policies

### Documentación
- `agents.md` — Arquitectura de agentes (3 roles)
- `.agents/skills/BIND_ERP_RULES.md` — Reglas de integración Bind ERP

## Features Terminadas ✅
- UI completa: Sidebar, Dashboard, Chat, KPICards, Charts
- Backend pipeline 4 agentes (Router → DataAnalyst → ReportGenerator → Supervisor)
- Bind ERP Client: todos los módulos (Ventas, Inventario, Compras, Contabilidad, Directorio)
- Cache manager con TTL y modo contingencia (stale)
- Rate limiter por tenant
- Auth middleware JWT
- Supabase migrations
- localStorage persistence del chat
- Guardrails de seguridad (SupervisorAgent — no data leakage)

## Pendiente / Blockers ⚠️
- `backend/.env` NO existe (solo `.env.example`)
- `frontend/.env.local` NO existe (solo `.env.local.example`)
- AuthProvider en DEMO MODE (token = "demo-token" → backend rechaza con 401)
- Función Supabase RPC `decrypt_bind_key` NO creada en migraciones
- LLM no integrado (`LLM_PROVIDER=none`) — respuestas genéricas sin IA real
- KPICards con datos hardcoded (mock)
