"use client";
import React from "react";
import { TrendingUp, Package, FileText, Users } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string;
  change: string;
  changeType: "up" | "down" | "neutral";
  icon: React.ReactNode;
}

function KPICard({ title, value, change, changeType, icon }: KPICardProps) {
  const changeColor =
    changeType === "up"
      ? "text-accent"
      : changeType === "down"
        ? "text-red-400"
        : "text-textPrimary/50";

  return (
    <div className="glass-panel rounded-xl p-5 hover:border-accent/20 transition-all duration-300 group hover:shadow-[0_0_20px_rgba(164,218,48,0.08)]">
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs text-textPrimary/60 uppercase tracking-wider font-medium">
          {title}
        </p>
        <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center group-hover:bg-accent/20 transition-colors">
          {icon}
        </div>
      </div>
      <p className="text-2xl font-bold text-textPrimary">{value}</p>
      <p className={`text-xs mt-1 ${changeColor}`}>{change}</p>
    </div>
  );
}

export default function KPICards() {
  // En producción: estos datos vendrán del backend via /api/dashboard/kpis
  const kpis = [
    {
      title: "Ventas del Mes",
      value: "$284,500",
      change: "↑ 12.4% vs mes anterior",
      changeType: "up" as const,
      icon: <TrendingUp size={16} className="text-accent" />,
    },
    {
      title: "Productos en Stock",
      value: "1,247",
      change: "↓ 3 bajo mínimo",
      changeType: "down" as const,
      icon: <Package size={16} className="text-accent" />,
    },
    {
      title: "Facturas Pendientes",
      value: "18",
      change: "$45,200 por cobrar",
      changeType: "neutral" as const,
      icon: <FileText size={16} className="text-accent" />,
    },
    {
      title: "Clientes Activos",
      value: "89",
      change: "↑ 5 nuevos este mes",
      changeType: "up" as const,
      icon: <Users size={16} className="text-accent" />,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {kpis.map((kpi, idx) => (
        <KPICard key={idx} {...kpi} />
      ))}
    </div>
  );
}
