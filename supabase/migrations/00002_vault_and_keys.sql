-- Create a private schema that is NOT exposed by PostgREST
CREATE SCHEMA IF NOT EXISTS api_keys_private;

-- Ensure pgcrypto is enabled
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA extensions;

-- Create table to store encrypted Bind ERP keys
CREATE TABLE api_keys_private.bind_erp_keys (
    tenant_id UUID PRIMARY KEY REFERENCES public.tenants(id) ON DELETE CASCADE,
    encrypted_token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- This table does NOT have RLS because it is in a private schema not accessible from the frontend.
-- Revoke all access from standard authenticated web users entirely.
REVOKE ALL ON SCHEMA api_keys_private FROM PUBLIC;
REVOKE ALL ON SCHEMA api_keys_private FROM authenticated;
REVOKE ALL ON SCHEMA api_keys_private FROM anon;

-- Grant usage to the service_role which the FastAPI backend will utilize
GRANT USAGE ON SCHEMA api_keys_private TO service_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA api_keys_private TO service_role;

-- Note for FastAPI Backend usage:
-- INSERT INTO api_keys_private.bind_erp_keys (tenant_id, encrypted_token) 
-- VALUES ('<tenant_id>', PGP_SYM_ENCRYPT('actual_token_here', current_setting('app.encryption_key')))
-- ON CONFLICT (tenant_id) DO UPDATE SET encrypted_token = EXCLUDED.encrypted_token;
--
-- SELECT tenant_id, PGP_SYM_DECRYPT(encrypted_token::bytea, current_setting('app.encryption_key')) as token 
-- FROM api_keys_private.bind_erp_keys WHERE tenant_id = '<tenant_id>';
