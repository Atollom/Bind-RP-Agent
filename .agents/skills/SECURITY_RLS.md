---
name: Supabase Security and RLS Rules
description: Reglas estrictas de seguridad (Zero Trust) y multi-tenant para Atollom AI usando Supabase.
---

# Reglas de Seguridad (Zero Trust y Multi-Tenant)

## Row Level Security (RLS)
- **Obligatorio:** Todas las tablas de la base de datos pública en Supabase deben tener habilitado Row Level Security (RLS).
- **Aislamiento Multi-Tenant:** Las políticas RLS deben asegurar que el "Cliente A" jamás pueda acceder o modificar los datos o sesiones del "Cliente B". Todas las consultas deben filtrar estrictamente basándose en el `tenant_id` asociado al usuario autenticado.
- Todas las tablas deben contener una columna `tenant_id` (UUID) como llave foránea.

## Gestión Segura de Credenciales (API Keys Vault)
- **Esquema Privado:** Se debe crear un esquema privado en PostgreSQL (ej. `api_keys_private`) para almacenar las API Keys de Bind ERP correspondientes a cada cliente.
- **Cifrado:** Las llaves deben guardarse cifradas en reposo usando extensiones criptográficas de PostgreSQL (ej. `pgcrypto`).
- **Acceso Restringido:** Este esquema privado NO debe ser expuesto a través de la API REST o GraphQL autogenerada por Supabase (PostgREST).
- **Prohibición Frontend:** Las llaves de la API de Bind ERP NUNCA deben viajar al frontend. Solo el backend en FastAPI debe consultar este esquema privado (o usar Edge Functions seguras) para inyectar los tokens al comunicarse con Bind.
