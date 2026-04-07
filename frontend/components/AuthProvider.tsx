"use client";
import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface AuthContextType {
  user: any;
  session: any;
  loading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  signOut: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null);
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem("atollom_token");
    if (!token) {
      router.push("/login");
      setLoading(false);
      return;
    }
    // Decodificar payload del JWT (sin verificar firma — la verificación es del backend)
    try {
      const payload = JSON.parse(atob(token.split(".")[1]));
      const isExpired = payload.exp && payload.exp * 1000 < Date.now();
      if (isExpired) {
        localStorage.removeItem("atollom_token");
        router.push("/login");
        setLoading(false);
        return;
      }
      setSession({ access_token: token });
      setUser({ id: payload.sub, email: payload.email || "admin", role: payload.role });
    } catch {
      localStorage.removeItem("atollom_token");
      router.push("/login");
    }
    setLoading(false);
  }, [router]);

  const signOut = async () => {
    localStorage.removeItem("atollom_token");
    setUser(null);
    setSession(null);
    router.push("/login");
  };

  if (loading) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-background">
        <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <AuthContext.Provider value={{ user, session, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
