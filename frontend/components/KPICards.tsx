"use client";
import React, { useEffect, useState } from "react";
import { TrendingUp, Package, FileText, Users, Loader2 } from "lucide-react";
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

export default function KPICards() {
  const { session } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchKPIs = async () => {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      try {
        // Consultas paralelas: inventario y clientes
        const [invRes, clientRes] = await Promise.all([
          fetch(`${apiUrl}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${session?.access_token}` },
            body: JSON.stringify({ message: "resumen inventario productos en stock" }),
          }),
          fetch(`${apiUrl}/api/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Authorization: `Bearer ${session?.access_token}` },
            body: JSON.stringify({ message: "cuántos clientes tengo en total" }),
          }),
        ]);

        const [invData, clientData] = await Promise.all([invRes.json(), clientRes.json()]);

        const invItems = invData?.response?.chartData?.length ?? 0;
        const clientItems = clientData?.response?.chartData?.length ?? 0;

        setData({ invItems, clientItems });
      } catch {
        setData({ invItems: null, clientItems: null });
      } finally {
        setLoading(false);
      }
    };

    if (session?.access_token) fetchKPIs();
  }, [session]);

  const kpis = [
    {
      title: "Ventas del Mes",
      value: "—",
      change: "Sin registros en Bind ERP",
      changeType: "neutral" as const,
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
      title: "Facturas Pendientes",
      value: "—",
      change: "Sin registros en Bind ERP",
      changeType: "neutral" as const,
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
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi, idx) => (
        <KPICard key={idx} {...kpi} loading={loading && (idx === 1 || idx === 3)} />
      ))}
    </div>
  );
}
