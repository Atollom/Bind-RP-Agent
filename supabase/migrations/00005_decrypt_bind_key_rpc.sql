-- ============================================================
-- MIGRACIÓN 00005: Función RPC para descifrar la API Key de Bind ERP
-- Llamada desde FastAPI: supabase.rpc("decrypt_bind_key", {"p_tenant_id": "..."})
-- ============================================================

CREATE OR REPLACE FUNCTION public.decrypt_bind_key(p_tenant_id UUID)
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = api_keys_private, extensions
AS $$
DECLARE
    v_token TEXT;
BEGIN
    SELECT PGP_SYM_DECRYPT(
        encrypted_token::bytea,
        current_setting('app.encryption_key')
    ) INTO v_token
    FROM api_keys_private.bind_erp_keys
    WHERE tenant_id = p_tenant_id;

    RETURN v_token;
END;
$$;

-- Seguridad: Solo service_role (backend FastAPI) puede ejecutar esta función.
REVOKE ALL ON FUNCTION public.decrypt_bind_key(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.decrypt_bind_key(UUID) FROM authenticated;
REVOKE ALL ON FUNCTION public.decrypt_bind_key(UUID) FROM anon;
GRANT EXECUTE ON FUNCTION public.decrypt_bind_key(UUID) TO service_role;

-- ============================================================
-- Función auxiliar: almacenar API Key cifrada para un tenant
-- Uso: supabase.rpc("store_bind_key", {"p_tenant_id": "...", "p_api_key": "..."})
-- ============================================================
CREATE OR REPLACE FUNCTION public.store_bind_key(p_tenant_id UUID, p_api_key TEXT)
RETURNS VOID
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = api_keys_private, extensions
AS $$
BEGIN
    INSERT INTO api_keys_private.bind_erp_keys (tenant_id, encrypted_token)
    VALUES (
        p_tenant_id,
        PGP_SYM_ENCRYPT(p_api_key, current_setting('app.encryption_key'))
    )
    ON CONFLICT (tenant_id) DO UPDATE
        SET encrypted_token = PGP_SYM_ENCRYPT(p_api_key, current_setting('app.encryption_key')),
            updated_at = NOW();
END;
$$;

REVOKE ALL ON FUNCTION public.store_bind_key(UUID, TEXT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.store_bind_key(UUID, TEXT) FROM authenticated;
REVOKE ALL ON FUNCTION public.store_bind_key(UUID, TEXT) FROM anon;
GRANT EXECUTE ON FUNCTION public.store_bind_key(UUID, TEXT) TO service_role;
