"use client";
import React, { useState, useEffect, useCallback } from "react";
import { Plus, Building2, Key, Mail, Lock, CheckCircle, AlertCircle, RefreshCw } from "lucide-react";
import { useAuth } from "./AuthProvider";

interface Client {
  tenant_id: string;
  company_name: string;
  email: string;
  has_bind_key: boolean;
  created_at: string;
}

export default function AdminPanel() {
  const { session } = useAuth();
  const [clients, setClients] = useState<Client[]>([]);
  const [loadingClients, setLoadingClients] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    company_name: "",
    email: "",
    password: "",
    bind_api_key: "",
  });

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchClients = useCallback(async () => {
    setLoadingClients(true);
    try {
      const res = await fetch(`${apiUrl}/api/admin/clients`, {
        headers: { Authorization: `Bearer ${session?.access_token}` },
      });
      if (res.ok) setClients(await res.json());
    } catch {
      // silencioso
    } finally {
      setLoadingClients(false);
    }
  }, [apiUrl, session]);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    setSuccess("");

    try {
      const res = await fetch(`${apiUrl}/api/admin/clients`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify(form),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error al registrar cliente.");

      setSuccess(`Cliente "${data.company_name}" registrado con éxito. Tenant ID: ${data.tenant_id}`);
      setForm({ company_name: "", email: "", password: "", bind_api_key: "" });
      setShowForm(false);
      fetchClients();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-textPrimary">Admin — Clientes</h2>
          <p className="text-sm text-textPrimary/50 mt-1">
            Registra y gestiona los clientes de Atollom AI conectados a Bind ERP
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchClients}
            className="p-2 rounded-lg text-textPrimary/50 hover:bg-white/5 transition-all"
            title="Actualizar"
          >
            <RefreshCw size={18} />
          </button>
          <button
            onClick={() => { setShowForm(!showForm); setError(""); setSuccess(""); }}
            className="flex items-center gap-2 px-4 py-2 bg-accent text-[#001C3E] rounded-xl font-semibold text-sm hover:bg-[#b5f532] transition-all shadow-[0_0_20px_rgba(164,218,48,0.3)]"
          >
            <Plus size={16} />
            Nuevo Cliente
          </button>
        </div>
      </div>

      {/* Mensajes */}
      {success && (
        <div className="flex items-start gap-3 bg-green-500/10 border border-green-500/30 text-green-400 text-sm rounded-xl px-4 py-3">
          <CheckCircle size={18} className="flex-shrink-0 mt-0.5" />
          <span>{success}</span>
        </div>
      )}
      {error && (
        <div className="flex items-start gap-3 bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-xl px-4 py-3">
          <AlertCircle size={18} className="flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Formulario alta cliente */}
      {showForm && (
        <form onSubmit={handleSubmit} className="glass-panel rounded-2xl p-6 border border-accent/20 space-y-4">
          <h3 className="text-lg font-semibold text-textPrimary mb-2">Registrar nuevo cliente</h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-textPrimary/60 mb-1.5 uppercase tracking-wider">
                <Building2 size={12} className="inline mr-1" />Empresa
              </label>
              <input
                required value={form.company_name}
                onChange={e => setForm(f => ({ ...f, company_name: e.target.value }))}
                placeholder="Nombre de la empresa"
                className="w-full bg-background/60 border border-white/10 rounded-xl px-4 py-2.5 text-textPrimary placeholder:text-textPrimary/30 outline-none focus:border-accent/50 transition-all text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-textPrimary/60 mb-1.5 uppercase tracking-wider">
                <Mail size={12} className="inline mr-1" />Email del cliente
              </label>
              <input
                required type="email" value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                placeholder="cliente@empresa.com"
                className="w-full bg-background/60 border border-white/10 rounded-xl px-4 py-2.5 text-textPrimary placeholder:text-textPrimary/30 outline-none focus:border-accent/50 transition-all text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-textPrimary/60 mb-1.5 uppercase tracking-wider">
                <Lock size={12} className="inline mr-1" />Contraseña temporal
              </label>
              <input
                required type="password" value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                placeholder="Mínimo 8 caracteres"
                minLength={8}
                className="w-full bg-background/60 border border-white/10 rounded-xl px-4 py-2.5 text-textPrimary placeholder:text-textPrimary/30 outline-none focus:border-accent/50 transition-all text-sm"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-textPrimary/60 mb-1.5 uppercase tracking-wider">
                <Key size={12} className="inline mr-1" />API Key de Bind ERP
              </label>
              <input
                required value={form.bind_api_key}
                onChange={e => setForm(f => ({ ...f, bind_api_key: e.target.value }))}
                placeholder="eyJhbGci..."
                className="w-full bg-background/60 border border-white/10 rounded-xl px-4 py-2.5 text-textPrimary placeholder:text-textPrimary/30 outline-none focus:border-accent/50 transition-all text-sm font-mono"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="button" onClick={() => setShowForm(false)}
              className="flex-1 px-4 py-2.5 rounded-xl border border-white/10 text-textPrimary/70 hover:bg-white/5 transition-all text-sm"
            >
              Cancelar
            </button>
            <button
              type="submit" disabled={submitting}
              className="flex-1 px-4 py-2.5 rounded-xl bg-accent text-[#001C3E] font-semibold hover:bg-[#b5f532] transition-all text-sm disabled:opacity-50"
            >
              {submitting ? "Registrando..." : "Registrar cliente"}
            </button>
          </div>
        </form>
      )}

      {/* Lista de clientes */}
      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-textPrimary/50 uppercase tracking-wider">
          Clientes registrados ({clients.length})
        </h3>

        {loadingClients ? (
          <div className="flex justify-center py-12">
            <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
          </div>
        ) : clients.length === 0 ? (
          <div className="glass-panel rounded-2xl p-8 text-center text-textPrimary/40">
            <Building2 size={32} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No hay clientes registrados aún.</p>
            <p className="text-xs mt-1">Usa el botón "Nuevo Cliente" para registrar el primero.</p>
          </div>
        ) : (
          clients.map(client => (
            <div key={client.tenant_id} className="glass-panel rounded-xl px-5 py-4 border border-white/5 flex items-center justify-between gap-4">
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center flex-shrink-0">
                  <Building2 size={18} className="text-accent" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-textPrimary">{client.company_name}</p>
                  <p className="text-xs text-textPrimary/50">{client.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs">
                <span className={`flex items-center gap-1 px-2 py-1 rounded-full border ${client.has_bind_key ? "border-green-500/30 bg-green-500/10 text-green-400" : "border-red-500/30 bg-red-500/10 text-red-400"}`}>
                  <Key size={10} />
                  {client.has_bind_key ? "Bind OK" : "Sin API Key"}
                </span>
                <span className="text-textPrimary/30 hidden md:block">
                  {new Date(client.created_at).toLocaleDateString("es-MX")}
                </span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
