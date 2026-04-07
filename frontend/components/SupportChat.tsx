"use client";
import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, User, Loader2, HeadphonesIcon } from "lucide-react";
import { useAuth } from "./AuthProvider";

interface Msg { role: "user" | "agent"; content: string; ts: number; }

const SUPPORT_SYSTEM = `Eres el agente de soporte técnico de Atollom AI. Ayudas a los usuarios con:
- Problemas de conexión con Bind ERP
- Preguntas sobre el dashboard y sus módulos
- Errores en el chat IA o exportaciones
- Configuración de API keys y tenants
- Dudas sobre facturación, inventario, reportes
Responde en español, de forma concisa y amable. Si es un problema técnico grave, indica que escalan a contacto@atollom.com.`;

export default function SupportChat() {
  const { session } = useAuth();
  const [messages, setMessages] = useState<Msg[]>([{
    role: "agent",
    content: "Hola, soy el agente de soporte de Atollom AI. ¿En qué puedo ayudarte hoy? Puedo asistirte con el dashboard, Bind ERP, exportaciones o cualquier problema técnico.",
    ts: Date.now(),
  }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: text, ts: Date.now() }]);
    setLoading(true);

    try {
      // Usar el chat del agente con contexto de soporte
      const supportQuery = `[SOPORTE TÉCNICO] ${text}`;
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${session?.access_token}` },
        body: JSON.stringify({ message: supportQuery }),
      });

      let reply = "Entendido. Para este tipo de consulta te recomiendo escribir directamente a contacto@atollom.com con el detalle del problema.";

      if (res.ok) {
        const data = await res.json();
        const content = data?.response?.content;
        if (content && !content.includes("No logré identificar")) {
          reply = content;
        } else {
          // Respuesta de soporte genérica si el agente no reconoce la query
          reply = generateSupportReply(text);
        }
      }

      setMessages(prev => [...prev, { role: "agent", content: reply, ts: Date.now() }]);
    } catch {
      setMessages(prev => [...prev, {
        role: "agent",
        content: "Tuve un problema al procesar tu consulta. Por favor escribe a contacto@atollom.com y te atenderemos a la brevedad.",
        ts: Date.now(),
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-3 p-4 border-b border-white/10 bg-black/20 flex-shrink-0">
        <div className="w-10 h-10 rounded-full bg-accent/15 flex items-center justify-center border border-accent/30">
          <HeadphonesIcon size={20} className="text-accent" />
        </div>
        <div>
          <h2 className="font-bold text-textPrimary">Soporte Atollom AI</h2>
          <p className="text-xs text-textPrimary/50">Asistente técnico disponible 24/7</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          <span className="text-xs text-green-400">En línea</span>
        </div>
      </div>

      {/* Mensajes */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-3 max-w-[85%] ${msg.role === "user" ? "ml-auto flex-row-reverse" : ""}`}>
            <div className={`w-8 h-8 flex-shrink-0 rounded-full flex items-center justify-center ${msg.role === "user" ? "bg-panel border border-white/20" : "bg-accent text-[#001C3E]"}`}>
              {msg.role === "user" ? <User size={14} /> : <Bot size={14} />}
            </div>
            <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.role === "user" ? "bg-panel border border-white/10" : "bg-accent/10 border border-accent/20 text-textPrimary"}`}>
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex gap-3 max-w-[85%]">
            <div className="w-8 h-8 rounded-full bg-accent text-[#001C3E] flex items-center justify-center">
              <Bot size={14} />
            </div>
            <div className="flex items-center gap-2 px-4 py-3 text-textPrimary/50 text-sm">
              <Loader2 size={14} className="animate-spin text-accent" />
              Analizando tu consulta...
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {/* Quick replies */}
      <div className="px-4 py-2 flex gap-2 flex-wrap flex-shrink-0">
        {["¿Cómo exportar a Excel?", "Error en el chat", "¿Cómo agrego un cliente?", "Problema con Bind ERP"].map(q => (
          <button key={q} onClick={() => { setInput(q); }}
            className="text-xs px-3 py-1.5 rounded-full border border-accent/20 text-accent/70 hover:bg-accent/10 transition-all">
            {q}
          </button>
        ))}
      </div>

      {/* Input */}
      <div className="p-4 flex-shrink-0">
        <div className="flex items-center gap-2 glass-panel rounded-full p-2 pl-5 pr-2 border-white/20">
          <input
            value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && send()}
            placeholder="Describe tu problema o pregunta..."
            disabled={loading}
            className="flex-1 bg-transparent border-none outline-none text-textPrimary placeholder:text-textPrimary/40 text-sm disabled:opacity-50"
          />
          <button onClick={send} disabled={!input.trim() || loading}
            className="bg-accent text-[#001C3E] p-3 rounded-full hover:scale-105 transition-all shadow-[0_0_15px_rgba(164,218,48,0.3)] disabled:opacity-50">
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}

function generateSupportReply(query: string): string {
  const q = query.toLowerCase();
  if (q.includes("excel") || q.includes("pdf") || q.includes("export")) {
    return "Para exportar: en el Chat IA, después de que el agente responda con datos, aparecerán botones de 'Exportar Excel' y 'Exportar PDF'. También puedes ir directamente a cada módulo (Ventas, Inventario, etc.) y usar los botones de exportación en la parte superior.";
  }
  if (q.includes("bind") || q.includes("api key") || q.includes("conectar")) {
    return "Para configurar la conexión con Bind ERP: ve a 'Admin Clientes' en el sidebar → registra o actualiza el cliente con su API Key de Bind ERP. Si el problema persiste, verifica que la API Key no haya expirado en el portal de Bind.";
  }
  if (q.includes("cliente") || q.includes("alta") || q.includes("registrar")) {
    return "Para dar de alta un cliente: ve a 'Admin Clientes' en el sidebar → botón 'Nuevo Cliente' → llena el formulario con el nombre de la empresa, email, contraseña temporal y su API Key de Bind ERP.";
  }
  if (q.includes("chat") || q.includes("no responde") || q.includes("error")) {
    return "Si el chat no responde: 1) Verifica que tengas conexión a internet. 2) Intenta cerrar sesión y volver a entrar. 3) Si el problema persiste, escribe a contacto@atollom.com con el mensaje de error exacto.";
  }
  return "Gracias por tu consulta. Para ayudarte mejor, ¿podrías describir con más detalle el problema que estás experimentando? También puedes escribirnos directamente a contacto@atollom.com.";
}
