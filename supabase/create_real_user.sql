-- ================================================================
-- Script: Crear usuario admin real en Neon para Atollom RP Agent
-- Ejecutar en: https://console.neon.tech → tu proyecto → SQL Editor
-- ================================================================

-- PASO 1: Crear tenant de Atollom
INSERT INTO public.tenants (id, name, is_active, created_at)
VALUES (
  gen_random_uuid(),
  'Atollom',
  TRUE,
  NOW()
)
ON CONFLICT DO NOTHING;

-- PASO 2: Crear usuario admin + asignar rol (todo en una transacción)
DO $$
DECLARE
  v_tenant_id UUID;
  v_user_id   UUID;
BEGIN
  -- Obtener el tenant más reciente
  SELECT id INTO v_tenant_id FROM public.tenants WHERE name = 'Atollom' LIMIT 1;

  -- Crear usuario admin
  -- Email: contacto@atollom.com
  -- Password: Atollom2026 (hash bcrypt rondas=12)
  INSERT INTO public.users (id, email, hashed_password, is_active, created_at)
  VALUES (
    gen_random_uuid(),
    'contacto@atollom.com',
    '$2b$12$tE.lzFB0bZYA7pLw2ubmauqabPSiX.lxA2kLfC091LiQtq1j49mDC',
    TRUE,
    NOW()
  )
  ON CONFLICT (email) DO UPDATE
    SET hashed_password = '$2b$12$tE.lzFB0bZYA7pLw2ubmauqabPSiX.lxA2kLfC091LiQtq1j49mDC',
        is_active = TRUE
  RETURNING id INTO v_user_id;

  -- Si no retornó id (por el DO UPDATE), obtenerlo
  IF v_user_id IS NULL THEN
    SELECT id INTO v_user_id FROM public.users WHERE email = 'contacto@atollom.com';
  END IF;

  -- Asignar rol admin
  INSERT INTO public.user_roles (user_id, tenant_id, role, created_at)
  VALUES (v_user_id, v_tenant_id, 'admin', NOW())
  ON CONFLICT DO NOTHING;

  RAISE NOTICE 'OK — user_id: %, tenant_id: %', v_user_id, v_tenant_id;
END $$;

-- PASO 3: Verificar resultado
SELECT
  u.email,
  u.is_active,
  ur.role,
  t.name AS tenant,
  t.id   AS tenant_id
FROM public.users u
JOIN public.user_roles ur ON ur.user_id = u.id
JOIN public.tenants     t  ON t.id = ur.tenant_id
WHERE u.email = 'contacto@atollom.com';

-- ================================================================
-- CREDENCIALES DE ACCESO:
--   URL:      https://bind-rp-agent.vercel.app
--   Email:    contacto@atollom.com
--   Password: Atollom2026
-- ================================================================
