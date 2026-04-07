"use client";
import React, { useState } from "react";
import {
  LayoutDashboard,
  MessageSquare,
  ShoppingCart,
  Package,
  Truck,
  Calculator,
  Users,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Settings,
  HeadphonesIcon,
} from "lucide-react";
import { useAuth } from "./AuthProvider";
import AtollomLogo from "./AtollomLogo";

interface SidebarProps {
  activeSection: string;
  onSectionChange: (section: string) => void;
}

const navItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "chat", label: "Chat IA", icon: MessageSquare },
  { id: "ventas", label: "Ventas", icon: ShoppingCart },
  { id: "inventario", label: "Inventario", icon: Package },
  { id: "compras", label: "Compras", icon: Truck },
  { id: "contabilidad", label: "Contabilidad", icon: Calculator },
  { id: "directorio", label: "Directorio", icon: Users },
];

const adminItems = [
  { id: "admin", label: "Admin Clientes", icon: Settings },
  { id: "soporte", label: "Soporte", icon: HeadphonesIcon },
];

export default function Sidebar({ activeSection, onSectionChange }: SidebarProps) {
  const [collapsed, setCollapsed] = useState(false);
  const { signOut } = useAuth();

  return (
    <aside
      className={`flex flex-col h-full bg-[#00122a] border-r border-white/5 transition-all duration-300 ${
        collapsed ? "w-16" : "w-60"
      }`}
    >
      {/* Brand */}
      <div className="flex items-center gap-3 p-4 border-b border-white/5">
        <div className="w-9 h-9 flex-shrink-0 flex items-center justify-center">
          <AtollomLogo size={36} className="text-accent" glowIntensity="medium" />
        </div>
        {!collapsed && (
          <span className="text-sm font-bold tracking-wide truncate">
            <span className="text-accent">Atollom</span>{" "}
            <span className="text-textPrimary/80">AI Agent Manager</span>
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-2 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all group ${
                isActive
                  ? "bg-accent/15 text-accent shadow-[0_0_10px_rgba(164,218,48,0.1)]"
                  : "text-textPrimary/60 hover:bg-white/5 hover:text-textPrimary"
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon size={18} className={isActive ? "text-accent" : "group-hover:text-accent/70"} />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </button>
          );
        })}
      </nav>

      {/* Admin Section */}
      <div className="px-2 pb-2 border-t border-white/5 pt-2">
        {!collapsed && (
          <p className="text-[10px] text-textPrimary/30 uppercase tracking-widest px-3 pb-1">
            Administración
          </p>
        )}
        {adminItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeSection === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSectionChange(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all group ${
                isActive
                  ? "bg-accent/15 text-accent shadow-[0_0_10px_rgba(164,218,48,0.1)]"
                  : "text-textPrimary/60 hover:bg-white/5 hover:text-textPrimary"
              }`}
              title={collapsed ? item.label : undefined}
            >
              <Icon size={18} className={isActive ? "text-accent" : "group-hover:text-accent/70"} />
              {!collapsed && <span className="truncate">{item.label}</span>}
            </button>
          );
        })}
      </div>

      {/* Footer */}
      <div className="p-2 border-t border-white/5 space-y-1">
        <button
          onClick={signOut}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-red-400/70 hover:bg-red-500/10 hover:text-red-400 transition-all"
          title={collapsed ? "Cerrar sesión" : undefined}
        >
          <LogOut size={18} />
          {!collapsed && <span>Cerrar sesión</span>}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center p-2 rounded-lg text-textPrimary/40 hover:bg-white/5 hover:text-textPrimary/70 transition-all"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
    </aside>
  );
}
