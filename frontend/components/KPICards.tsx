"use client";
import React, { useEffect, useState, useCallback } from "react";
import { TrendingUp, Package, FileText, Users, Loader2, RefreshCw } from "lucide-react";
import { useAuth } from "./AuthProvider";

interface KPICardProps {
  title: string;
  value: string;
  change: string;
  changeType: "up" | "down" | "neutral";
  icon: React.ReactNode;
  loading?: boolean;
}

function KPICard({ title, value, change, changeType, icon, loading }: KPICardProps) {
  const changeColor =
    changeType === "up"
      ? "text-accent"
      : changeType === "down"
        ? "text-red-400"
        : "text-textPrimary/50";

  return (
    <div className="glass-panel rounded-xl p-5 hover:border-accent/20 transition-all duration-300 group hover:shadow-[0_0_20px_rgba(164,218,48,0.08)]">
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs text-textPrimary/60 uppercase tracking-wider font-medium">{title}</p>
        <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
          {icon}
        </div>
      </div>
      {loading ? (
        <div className="flex items-center gap-2 mt-2">
          <Loader2 size={16} className="animate-spin text-accent" />
          <span className="text-textPrimary/30 text-sm">Cargando...</span>
        </div>
      ) : (
        <>
          <p className="text-2xl font-bold text-textPrimary">{value}</p>
          <p className={`text-xs mt-1 ${changeColor}`}>{change}</p>
        </>
      )}
    </div>
  );
}

interface KPIData {
  invItems: number | null;
  clientItems: number | null;
  invoiceItems: number | null;
  accountItems: number | null;
}

async function fetchModule(apiUrl: string, token: string, message: string) {
  try {
    const res = await fetch(`${apiUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export default function KPICards() {
  const { session } = useAuth();
  const [data, setData] = useState<KPIData | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const fetchKPIs = useCallback(async () => {
    if (!session?.access_token) return;
    setLoading(true);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const token = session.access_token;

    // Consultas paralelas — 4 módulos simultáneos
    const [invData, clientData, invoiceData, accountData] = await Promise.all([
      fetchModule(apiUrl, token, "cuántos productos tengo en inventario"),
      fetchModule(apiUrl, token, "cuántos clientes tengo en total"),
      fetchModule(apiUrl, token, "cuántas facturas o ventas tengo registradas"),
      fetchModule(apiUrl, token, "resumen de mis activos y cuentas contables"),
    ]);

    const invItems =
      invData?.response?.chartData?.length ??
      invData?.response?.data?.length ??
      null;

    const clientItems =
      clientData?.response?.chartData?.length ??
      clientData?.response?.data?.length ??
      null;

    const invoiceItems =
      invoiceData?.response?.chartData?.length ??
      invoiceData?.response?.data?.length ??
      null;

    const accountItems =
      accountData?.response?.chartData?.length ??
      accountData?.response?.data?.length ??
      null;

    setData({ invItems, clientItems, invoiceItems, accountItems });
    setLastUpdated(new Date().toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" }));
    setLoading(false);
  }, [session]);

  // Fetch inicial
  useEffect(() => {
    fetchKPIs();
  }, [fetchKPIs]);

  // Auto-refresh cada 5 minutos
  useEffect(() => {
    const interval = setInterval(fetchKPIs, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchKPIs]);

  const kpis = [
    {
      title: "Ventas / Facturas",
      value: loading ? "—" : data?.invoiceItems != null ? `${data.invoiceItems}` : "0",
      change: loading ? "" : data?.invoiceItems != null ? `${data.invoiceItems} registros en Bind ERP` : "Sin registros en Bind ERP",
      changeType: (data?.invoiceItems && data.invoiceItems > 0 ? "up" : "neutral") as "up" | "neutral",
      icon: <TrendingUp size={16} className="text-accent" />,
    },
    {
      title: "Productos en Stock",
      value: loading ? "—" : data?.invItems != null ? `${data.invItems}` : "—",
      change: loading ? "" : data?.invItems != null ? `${data.invItems} productos en Bind ERP` : "Sin datos",
      changeType: "neutral" as const,
      icon: <Package size={16} className="text-accent" />,
    },
    {
      title: "Cuentas Contables",
      value: loading ? "—" : data?.accountItems != null ? `${data.accountItems}` : "—",
      change: loading ? "" : data?.accountItems != null ? `${data.accountItems} cuentas activas` : "Sin datos",
      changeType: (data?.accountItems && data.accountItems > 0 ? "up" : "neutral") as "up" | "neutral",
      icon: <FileText size={16} className="text-accent" />,
    },
    {
      title: "Clientes en Directorio",
      value: loading ? "—" : data?.clientItems != null ? `${data.clientItems}` : "—",
      change: loading ? "" : data?.clientItems != null ? `${data.clientItems} registros en Bind ERP` : "Sin datos",
      changeType: "neutral" as const,
      icon: <Users size={16} className="text-accent" />,
    },
  ];

  return (
    <div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi, idx) => (
          <KPICard key={idx} {...kpi} loading={loading} />
        ))}
      </div>
      {/* Footer con último update y refresh manual */}
      <div className="flex items-center justify-end gap-2 mt-2">
        {lastUpdated && (
          <span className="text-[10px] text-textPrimary/30">
            Actualizado: {lastUpdated}
          </span>
        )}
        <button
          onClick={fetchKPIs}
          disabled={loading}
          className="flex items-center gap-1 text-[10px] text-textPrimary/30 hover:text-accent/60 transition-colors disabled:opacity-30"
          title="Actualizar KPIs"
        >
          <RefreshCw size={10} className={loading ? "animate-spin" : ""} />
          Actualizar
        </button>
      </div>
    </div>
  );
}
