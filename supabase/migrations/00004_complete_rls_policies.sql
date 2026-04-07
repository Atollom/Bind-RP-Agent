-- ============================================================
-- MIGRACIÓN 00004: Completar políticas RLS para Multi-Tenant
-- Cierra brechas de INSERT, UPDATE y DELETE identificadas en auditoría.
-- ============================================================

-- ============================================================
-- TABLA: public.usage_logs
-- Solo el backend (service_role) puede insertar logs.
-- Los usuarios autenticados ya pueden leer los suyos (migración 00003).
-- ============================================================
CREATE POLICY "Only backend can insert usage logs" ON public.usage_logs
    FOR INSERT TO service_role
    WITH CHECK (true);

-- ============================================================
-- TABLA: public.user_roles
-- Solo admins del tenant pueden insertar o actualizar roles.
-- ============================================================
CREATE POLICY "Admins can insert roles in their tenant" ON public.user_roles
    FOR INSERT TO authenticated
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.tenant_id = user_roles.tenant_id
            AND ur.user_id = auth.uid()
            AND ur.role = 'admin'
        )
    );

CREATE POLICY "Admins can update roles in their tenant" ON public.user_roles
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.tenant_id = user_roles.tenant_id
            AND ur.user_id = auth.uid()
            AND ur.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.tenant_id = user_roles.tenant_id
            AND ur.user_id = auth.uid()
            AND ur.role = 'admin'
        )
    );

-- ============================================================
-- TABLA: public.tenants
-- Solo admins de un tenant pueden actualizar su nombre.
-- Nadie puede eliminar tenants desde el frontend.
-- ============================================================
CREATE POLICY "Admins can update their own tenant" ON public.tenants
    FOR UPDATE TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.tenant_id = tenants.id
            AND ur.user_id = auth.uid()
            AND ur.role = 'admin'
        )
    )
    WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.user_roles ur
            WHERE ur.tenant_id = tenants.id
            AND ur.user_id = auth.uid()
            AND ur.role = 'admin'
        )
    );

-- ============================================================
-- BLOQUEO EXPLÍCITO DE DELETE en tablas sensibles.
-- Nadie (excepto service_role vía backend) puede borrar registros.
-- ============================================================
CREATE POLICY "No delete on tenants" ON public.tenants
    FOR DELETE TO authenticated
    USING (false);

CREATE POLICY "No delete on user_roles" ON public.user_roles
    FOR DELETE TO authenticated
    USING (false);

CREATE POLICY "No delete on usage_logs" ON public.usage_logs
    FOR DELETE TO authenticated
    USING (false);
