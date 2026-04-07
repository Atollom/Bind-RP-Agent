-- Enable uuid extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tenants table
CREATE TABLE public.tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create table linking users to tenants
-- auth.users is the native Supabase GoTrue table
CREATE TABLE public.user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, tenant_id)
);

-- Enable RLS
ALTER TABLE public.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;

-- Policies for public.tenants
-- Only users that belong to a tenant can view its details
CREATE POLICY "Users can view their own tenant" ON public.tenants
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.tenant_id = tenants.id
            AND ur.user_id = auth.uid()
        )
    );

-- Policies for public.user_roles
-- Users can view roles within their own tenant
CREATE POLICY "Users can view roles in their tenant" ON public.user_roles
    FOR SELECT TO authenticated
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.user_roles
            WHERE user_id = auth.uid()
        )
    );
