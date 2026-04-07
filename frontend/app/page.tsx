"use client";
import React, { useState } from "react";
import Sidebar from "@/components/Sidebar";
import ChatDashboard from "@/components/ChatDashboard";
import KPICards from "@/components/KPICards";
import AuthProvider from "@/components/AuthProvider";
import MultiChartVisualizer from "@/components/MultiChartVisualizer";
import AdminPanel from "@/components/AdminPanel";

// Datos de ejemplo para el dashboard principal (vendrán del backend en producción)
const weeklySalesData = [
  { name: "Lun", value: 12400 },
  { name: "Mar", value: 15800 },
  { name: "Mié", value: 9200 },
  { name: "Jue", value: 18300 },
  { name: "Vie", value: 21500 },
  { name: "Sáb", value: 8700 },
  { name: "Dom", value: 4200 },
];

const inventoryData = [
  { name: "Ortopedia", value: 340 },
  { name: "Rehabilitación", value: 280 },
  { name: "Consumibles", value: 520 },
  { name: "Equipo Médico", value: 107 },
];

function DashboardContent() {
  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <div>
        <h2 className="text-2xl font-bold text-textPrimary">Dashboard</h2>
        <p className="text-sm text-textPrimary/50 mt-1">
          Resumen operativo en tiempo real desde Bind ERP
        </p>
      </div>

      <KPICards />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-semibold text-textPrimary/70 mb-1 uppercase tracking-wider">
            Ventas de la Semana
          </h3>
          <MultiChartVisualizer data={weeklySalesData} chartType="area" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-textPrimary/70 mb-1 uppercase tracking-wider">
            Distribución de Inventario
          </h3>
          <MultiChartVisualizer data={inventoryData} chartType="pie" />
        </div>
      </div>
    </div>
  );
}

function ComingSoonContent({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="flex-1 flex items-center justify-center text-textPrimary/40">
      <div className="text-center">
        <p className="text-4xl mb-3">🚧</p>
        <p className="text-lg font-semibold">{title}</p>
        <p className="text-sm mt-1">{subtitle || "Este módulo estará disponible próximamente."}</p>
        <p className="text-xs mt-3 text-textPrimary/30">
          Usa el Chat IA para consultar datos de este módulo ahora mismo.
        </p>
      </div>
    </div>
  );
}

function AppContent() {
  const [activeSection, setActiveSection] = useState("dashboard");

  const renderContent = () => {
    switch (activeSection) {
      case "dashboard":
        return <DashboardContent />;
      case "chat":
        return <ChatDashboard />;
      case "ventas":
        return <ComingSoonContent title="Módulo de Ventas" />;
      case "inventario":
        return <ComingSoonContent title="Módulo de Inventario" />;
      case "compras":
        return <ComingSoonContent title="Módulo de Compras" />;
      case "contabilidad":
        return <ComingSoonContent title="Módulo de Contabilidad" />;
      case "directorio":
        return <ComingSoonContent title="Módulo de Directorio" />;
      case "admin":
        return <AdminPanel />;
      case "soporte":
        return <ComingSoonContent title="Soporte Atollom" subtitle="Agente de soporte disponible próximamente. Mientras tanto escríbenos a contacto@atollom.com" />;
      default:
        return <DashboardContent />;
    }
  };

  return (
    <div className="flex h-screen w-full overflow-hidden">
      <Sidebar activeSection={activeSection} onSectionChange={setActiveSection} />
      <main className="flex-1 flex flex-col overflow-hidden relative">
        {/* Glow backgrounds */}
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-accent/10 blur-[150px] pointer-events-none rounded-full" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-[#00A3FF]/10 blur-[150px] pointer-events-none rounded-full" />
        <div className="relative z-10 flex-1 overflow-hidden">{renderContent()}</div>
      </main>
    </div>
  );
}

export default function Home() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
