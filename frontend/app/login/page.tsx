"use client";
import React, { useState } from "react";
import { createClient } from "@/lib/supabase";
import AtollomLogo from "@/components/AtollomLogo";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const supabase = createClient();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const { error } = await supabase.auth.signInWithPassword({ email, password });

    if (error) {
      setError("Credenciales incorrectas. Verifica tu email y contraseña.");
      setLoading(false);
    } else {
      window.location.href = "/";
    }
  };

  return (
    <main className="w-full min-h-screen flex items-center justify-center relative overflow-hidden bg-background p-4">
      {/* Background glow effects */}
      <div className="absolute top-[-30%] left-[-15%] w-[50%] h-[50%] bg-accent/15 blur-[150px] pointer-events-none rounded-full" />
      <div className="absolute bottom-[-30%] right-[-15%] w-[50%] h-[50%] bg-[#00A3FF]/15 blur-[150px] pointer-events-none rounded-full" />

      <div className="w-full max-w-md relative z-10">
        {/* Logo / Brand */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-20 h-20 flex items-center justify-center mb-4">
            <AtollomLogo size={72} className="text-accent" glowIntensity="strong" />
          </div>
          <h1 className="text-3xl font-bold tracking-wide">
            <span className="text-accent">ATOLLOM</span>{" "}
            <span className="text-textPrimary/80">AI</span>
          </h1>
          <p className="text-textPrimary/60 text-sm mt-1">
            Inteligencia financiera para tu empresa
          </p>
        </div>

        {/* Login Card */}
        <form
          onSubmit={handleLogin}
          className="glass-panel rounded-2xl p-8 space-y-6 border border-white/10"
        >
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-textPrimary/80 mb-2">
              Correo electrónico
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@tuempresa.com"
              required
              className="w-full bg-background/60 border border-white/10 rounded-xl px-4 py-3 text-textPrimary placeholder:text-textPrimary/30 outline-none focus:border-accent/50 focus:shadow-[0_0_15px_rgba(164,218,48,0.15)] transition-all text-sm"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-textPrimary/80 mb-2">
              Contraseña
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              className="w-full bg-background/60 border border-white/10 rounded-xl px-4 py-3 text-textPrimary placeholder:text-textPrimary/30 outline-none focus:border-accent/50 focus:shadow-[0_0_15px_rgba(164,218,48,0.15)] transition-all text-sm"
            />
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-xl px-4 py-3">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent text-[#001C3E] font-semibold py-3 rounded-xl hover:bg-[#b5f532] hover:scale-[1.02] transition-all shadow-[0_0_25px_rgba(164,218,48,0.4)] disabled:opacity-50 disabled:hover:scale-100 text-sm"
          >
            {loading ? "Verificando..." : "Iniciar sesión"}
          </button>

          <p className="text-center text-textPrimary/40 text-xs mt-4">
            © {new Date().getFullYear()} Atollom AI · Gestión Tecnológica
          </p>
        </form>
      </div>
    </main>
  );
}
