"use client";
import React, { useState, useRef, useEffect, useCallback } from "react";
import { Send, Bot, User, Loader2, Trash2, History } from "lucide-react";
import { useAuth } from "./AuthProvider";
import MultiChartVisualizer from "./MultiChartVisualizer";
import AtollomLogo from "./AtollomLogo";

// =====================================================================
// INTERFACES
// =====================================================================
interface Message {
  id: string;
  role: "user" | "system";
  content: string;
  chartData?: any[] | null;
  chart_type?: string;
  is_stale?: boolean;
  timestamp: number;
}

// =====================================================================
// LOCAL STORAGE PERSISTENCE
// =====================================================================
const STORAGE_KEY = "atollom_chat_history";
const MAX_STORED_MESSAGES = 100; // Limitar para no abusar de localStorage

function loadChatHistory(): Message[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Message[];
    // Filtrar mensajes corruptos
    return parsed.filter(
      (m) => m && m.role && m.content && typeof m.content === "string"
    );
  } catch {
    return [];
  }
}

function saveChatHistory(messages: Message[]): void {
  if (typeof window === "undefined") return;
  try {
    // Solo guardar mensajes de texto (los chartData no se persisten bien en localStorage)
    const toSave = messages.slice(-MAX_STORED_MESSAGES).map((m) => ({
      ...m,
      chartData: null, // No persistir datos de gráficas (pueden ser muy grandes)
    }));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
  } catch {
    // localStorage lleno o no disponible — fallar silenciosamente
  }
}

function clearChatHistory(): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // No-op
  }
}

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

// =====================================================================
// WELCOME MESSAGE
// =====================================================================
const WELCOME_MESSAGE: Message = {
  id: "welcome",
  role: "system",
  content:
    "Hola. Soy tu asistente financiero de Atollom AI conectado a Bind ERP. Pregúntame sobre tus ventas, inventario, compras o contabilidad.",
  timestamp: Date.now(),
};

// =====================================================================
// COMPONENT
// =====================================================================
export default function ChatDashboard() {
  const { session } = useAuth();
  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showClearConfirm, setShowClearConfirm] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Cargar historial al montar
  useEffect(() => {
    const saved = loadChatHistory();
    if (saved.length > 0) {
      setMessages([WELCOME_MESSAGE, ...saved]);
    }
  }, []);

  // Guardar al cambiar mensajes (excepto el mount inicial)
  const isFirstLoad = useRef(true);
  useEffect(() => {
    if (isFirstLoad.current) {
      isFirstLoad.current = false;
      return;
    }
    // No guardar el mensaje de bienvenida
    const toSave = messages.filter((m) => m.id !== "welcome");
    saveChatHistory(toSave);
  }, [messages]);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleClearHistory = () => {
    clearChatHistory();
    setMessages([WELCOME_MESSAGE]);
    setShowClearConfirm(false);
    inputRef.current?.focus();
  };

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    const userMsg: Message = {
      id: generateId(),
      role: "user",
      content: userMessage,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session?.access_token}`,
        },
        body: JSON.stringify({ message: userMessage }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => null);
        throw new Error(errorData?.detail || `Error ${res.status}`);
      }

      const data = await res.json();

      let staleNotice = "";
      if (data.is_stale) {
        staleNotice =
          "\n\n⚠️ *Modo Contingencia: Datos servidos desde caché temporal para proteger tu cuota de Bind ERP.*";
      }

      const systemMsg: Message = {
        id: generateId(),
        role: "system",
        content:
          (data.response?.content || "Sin respuesta del servidor.") +
          staleNotice,
        chartData: data.response?.chartData,
        chart_type: data.response?.chart_type || "bar",
        is_stale: data.is_stale,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, systemMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: generateId(),
        role: "system",
        content: `No pude conectarme al servidor. ${err.message || "Intenta de nuevo en unos momentos."}`,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  // Formato de hora para los mensajes
  const formatTime = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString("es-MX", {
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="flex items-center justify-between p-4 border-b border-white/10 bg-black/20 flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-accent/15 flex items-center justify-center border border-accent/30 shadow-[0_0_15px_rgba(164,218,48,0.25)]">
            <AtollomLogo size={28} className="text-accent" glowIntensity="subtle" />
          </div>
          <div>
            <h1 className="text-xl font-bold">
              <span className="text-accent">ATOLLOM</span>{" "}
              <span className="text-textPrimary/80">AI</span>
            </h1>
            <p className="text-xs text-textPrimary/70">Conectado a Bind ERP</p>
          </div>
        </div>

        {/* Header Actions */}
        <div className="flex items-center gap-1 relative">
          {messages.filter((m) => m.id !== "welcome").length > 0 && (
            <div className="flex items-center gap-1 mr-2 text-textPrimary/40 text-xs">
              <History size={12} />
              <span>{messages.filter((m) => m.id !== "welcome").length} msgs</span>
            </div>
          )}
          <button
            onClick={() => setShowClearConfirm(true)}
            className="p-2 hover:bg-white/5 rounded-full transition-colors group"
            title="Limpiar historial"
          >
            <Trash2 size={18} className="text-textPrimary/40 group-hover:text-red-400 transition-colors" />
          </button>
        </div>
      </header>

      {/* Clear Confirmation Modal */}
      {showClearConfirm && (
        <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="glass-panel rounded-2xl p-6 max-w-sm mx-4 border border-white/10 shadow-2xl">
            <h3 className="text-textPrimary font-semibold text-lg mb-2">
              ¿Limpiar historial?
            </h3>
            <p className="text-textPrimary/60 text-sm mb-5">
              Se eliminarán todos los mensajes de esta conversación. Esta acción no se puede deshacer.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="flex-1 px-4 py-2.5 rounded-xl border border-white/10 text-textPrimary/70 hover:bg-white/5 transition-all text-sm"
              >
                Cancelar
              </button>
              <button
                onClick={handleClearHistory}
                className="flex-1 px-4 py-2.5 rounded-xl bg-red-500/20 border border-red-500/30 text-red-400 hover:bg-red-500/30 transition-all text-sm font-medium"
              >
                Limpiar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Chat Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 max-w-[95%] md:max-w-[80%] ${msg.role === "user" ? "ml-auto flex-row-reverse" : ""}`}
          >
            {/* Avatar */}
            <div
              className={`w-8 h-8 flex-shrink-0 rounded-full flex items-center justify-center shadow-lg ${msg.role === "user" ? "bg-panel border border-white/20" : "bg-accent text-[#001C3E]"}`}
            >
              {msg.role === "user" ? (
                <User size={16} className="text-textPrimary" />
              ) : (
                <Bot size={16} />
              )}
            </div>

            {/* Bubble */}
            <div
              className={`flex flex-col ${msg.role === "user" ? "items-end" : "items-start"} max-w-full`}
            >
              <div
                className={`px-4 py-3 rounded-2xl md:text-md text-sm leading-relaxed ${msg.role === "user" ? "bg-panel border border-white/10 shadow-lg" : "bg-transparent text-textPrimary"}`}
              >
                {msg.content}
              </div>

              {/* Timestamp */}
              {msg.id !== "welcome" && msg.timestamp && (
                <span className="text-[10px] text-textPrimary/30 mt-1 px-1">
                  {formatTime(msg.timestamp)}
                </span>
              )}

              {/* Chart */}
              {msg.chartData && msg.chartData.length > 0 && (
                <div className="w-full min-w-[280px] sm:min-w-[400px]">
                  <MultiChartVisualizer
                    data={msg.chartData}
                    chartType={msg.chart_type || "bar"}
                  />
                </div>
              )}
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isLoading && (
          <div className="flex gap-3 max-w-[80%]">
            <div className="w-8 h-8 flex-shrink-0 rounded-full flex items-center justify-center bg-accent text-[#001C3E]">
              <Bot size={16} />
            </div>
            <div className="flex items-center gap-2 px-4 py-3 text-textPrimary/60 text-sm">
              <Loader2 size={16} className="animate-spin text-accent" />
              <span>Analizando tus datos...</span>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-gradient-to-t from-background to-transparent pt-8 flex-shrink-0">
        <div className="flex items-center gap-2 glass-panel rounded-full p-2 pl-5 pr-2 border-white/20 shadow-xl">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="Pregúntale a Atollom AI sobre tu negocio..."
            disabled={isLoading}
            className="flex-1 bg-transparent border-none outline-none text-textPrimary placeholder:text-textPrimary/50 text-sm md:text-base font-light disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            className="bg-accent text-[#001C3E] p-3 rounded-full hover:scale-105 hover:bg-[#b5f532] transition-all shadow-[0_0_20px_rgba(164,218,48,0.4)] disabled:opacity-50"
            disabled={!input.trim() || isLoading}
          >
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}
