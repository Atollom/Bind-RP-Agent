-- ============================================================
-- NEON MIGRATION 002 — Funciones de cifrado para API Keys
-- Reemplaza el vault privado de Supabase con pgcrypto en Neon
-- ============================================================

-- Almacenar API Key de Bind cifrada para un tenant
CREATE OR REPLACE FUNCTION public.store_bind_key(
    p_tenant_id     UUID,
    p_api_key       TEXT,
    p_encrypt_key   TEXT
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO public.bind_erp_keys (tenant_id, encrypted_token)
    VALUES (
        p_tenant_id,
        encode(pgp_sym_encrypt(p_api_key, p_encrypt_key), 'base64')
    )
    ON CONFLICT (tenant_id) DO UPDATE
        SET encrypted_token = encode(pgp_sym_encrypt(p_api_key, p_encrypt_key), 'base64'),
            updated_at = NOW();
END;
$$;

-- Recuperar y descifrar API Key de Bind para un tenant
CREATE OR REPLACE FUNCTION public.decrypt_bind_key(
    p_tenant_id     UUID,
    p_encrypt_key   TEXT
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_encrypted TEXT;
BEGIN
    SELECT encrypted_token INTO v_encrypted
    FROM public.bind_erp_keys
    WHERE tenant_id = p_tenant_id;

    IF NOT FOUND THEN
        RETURN NULL;
    END IF;

    RETURN pgp_sym_decrypt(decode(v_encrypted, 'base64'), p_encrypt_key);
EXCEPTION
    WHEN OTHERS THEN
        RAISE WARNING 'decrypt_bind_key error para tenant %: %', p_tenant_id, SQLERRM;
        RETURN NULL;
END;
$$;

-- Registrar tenant de prueba para dev (idempotente)
-- Se puede eliminar en producción
INSERT INTO public.tenants (id, name)
VALUES ('00000000-0000-0000-0000-000000000001', 'Dev Tenant')
ON CONFLICT (id) DO NOTHING;
