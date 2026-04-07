-- ================================================================
-- Script: Crear usuario real en Neon para Atollom RP Agent
-- Ejecutar en: Neon Dashboard → SQL Editor
-- URL: https://console.neon.tech → bind-rp-agent → SQL Editor
-- ================================================================

-- PASO 1: Crear tenant real (tu empresa)
INSERT INTO public.tenants (id, name, is_active, created_at)
VALUES (
  gen_random_uuid(),
  'Atollom Demo',  -- ← Cambia esto por el nombre real de la empresa
  TRUE,
  NOW()
)
ON CONFLICT DO NOTHING
RETURNING id, name;

-- PASO 2: Guardar el tenant_id del paso anterior para usarlo abajo
-- (copia el UUID que devolvió el INSERT y pégalo en $TENANT_ID$)

-- PASO 3: Crear usuario admin con password hasheada
-- Password actual en este script: "Admin2025!"
-- Hash generado con bcrypt rondas=12
-- Para cambiar la password, ir a: https://bcrypt-generator.com (12 rounds)
DO $$
DECLARE
  v_tenant_id UUID;
  v_user_id   UUID;
BEGIN
  -- Obtener el tenant más reciente (el que acabas de crear)
  SELECT id INTO v_tenant_id FROM public.tenants ORDER BY created_at DESC LIMIT 1;

  -- Crear usuario
  INSERT INTO public.users (id, email, hashed_password, is_active, created_at)
  VALUES (
    gen_random_uuid(),
    'admin@atollom.ai',  -- ← Cambia por el email real
    '$2b$12$LQv3c1yqBqVHSbhzIKiQW.7KFkHyMRFl6wIBUbLBl8xhMwDOVjlb2',  -- "Admin2025!"
    TRUE,
    NOW()
  )
  ON CONFLICT (email) DO NOTHING
  RETURNING id INTO v_user_id;

  -- Si el usuario ya existía, obtener su id
  IF v_user_id IS NULL THEN
    SELECT id INTO v_user_id FROM public.users WHERE email = 'admin@atollom.ai';
  END IF;

  -- Asignar rol admin al tenant
  INSERT INTO public.user_roles (user_id, tenant_id, role, created_at)
  VALUES (v_user_id, v_tenant_id, 'admin', NOW())
  ON CONFLICT DO NOTHING;

  RAISE NOTICE 'Usuario creado: % → tenant: %', v_user_id, v_tenant_id;
END $$;

-- PASO 4: Verificar que todo quedó bien
SELECT
  u.email,
  u.is_active,
  ur.role,
  t.name AS tenant_name,
  t.id AS tenant_id
FROM public.users u
JOIN public.user_roles ur ON ur.user_id = u.id
JOIN public.tenants t ON t.id = ur.tenant_id
WHERE u.email = 'admin@atollom.ai';

-- ================================================================
-- RESULTADO ESPERADO:
-- email            | is_active | role  | tenant_name   | tenant_id
-- -----------------+-----------+-------+---------------+----------
-- admin@atollom.ai | true      | admin | Atollom Demo  | <uuid>
--
-- LOGIN EN LA APP:
-- Email:    admin@atollom.ai
-- Password: Admin2025!
-- ================================================================
