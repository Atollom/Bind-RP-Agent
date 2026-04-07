-- ============================================================
-- NEON MIGRATION 001 — Schema principal (Bind RP Agent)
-- PostgreSQL puro: sin roles Supabase, sin schema auth
-- uuid usa gen_random_uuid() nativo de PG13+
-- ============================================================

-- Extensiones disponibles en Neon
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── Tenants (empresas clientes) ──────────────────────────────
CREATE TABLE IF NOT EXISTS public.tenants (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ── Usuarios (auth propio, sin Supabase) ─────────────────────
CREATE TABLE IF NOT EXISTS public.users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ── Roles de usuario por tenant ───────────────────────────────
CREATE TABLE IF NOT EXISTS public.user_roles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES public.users(id) ON DELETE CASCADE,
    tenant_id   UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    role        TEXT NOT NULL CHECK (role IN ('admin', 'user')),
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(user_id, tenant_id)
);

-- ── API Keys de Bind ERP (cifradas con pgcrypto) ─────────────
CREATE TABLE IF NOT EXISTS public.bind_erp_keys (
    tenant_id       UUID PRIMARY KEY REFERENCES public.tenants(id) ON DELETE CASCADE,
    encrypted_token TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- ── Logs de uso ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.usage_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    endpoint_called TEXT NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('success', 'error', 'rate_limit', 'cache_hit')),
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- Índices para queries frecuentes
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id   ON public.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_user_roles_tenant_id ON public.user_roles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_tenant_id ON public.usage_logs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_usage_logs_created   ON public.usage_logs(created_at DESC);
