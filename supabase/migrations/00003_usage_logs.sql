-- Create usage_logs table to track API consumption
CREATE TABLE public.usage_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    endpoint_called TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'error', 'rate_limit', 'cache_hit')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable RLS
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;

-- Policies for public.usage_logs
-- Tenants can view their own consumption logs
CREATE POLICY "Users can view usage logs in their tenant" ON public.usage_logs
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.tenant_id = usage_logs.tenant_id
            AND ur.user_id = auth.uid()
        )
    );
