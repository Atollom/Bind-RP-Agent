"use client";
import React, { createContext, useContext, useState } from "react";

// ============================================================
// 🔶 DEMO MODE — Bypass de autenticación para preview del UI
//    Para restaurar auth real, descomentar el código original
//    y eliminar este bloque de demo.
// ============================================================

interface AuthContextType {
  user: any;
  session: any;
  loading: boolean;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: false,
  signOut: async () => {},
});

export const useAuth = () => useContext(AuthContext);

export default function AuthProvider({ children }: { children: React.ReactNode }) {
  const [loading] = useState(false);

  // Usuario simulado para demo
  const demoUser = {
    id: "demo-user-001",
    email: "demo@atollom.ai",
    user_metadata: { full_name: "Carlos Demo" },
  };

  const demoSession = {
    access_token: process.env.NEXT_PUBLIC_DEV_BYPASS_TOKEN || "dev-bypass-2025",
    user: demoUser,
  };

  const signOut = async () => {
    console.log("Demo mode: signOut llamado (sin efecto)");
  };

  return (
    <AuthContext.Provider value={{ user: demoUser, session: demoSession, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

// ============================================================
// 🔒 CÓDIGO ORIGINAL (restaurar cuando Supabase esté listo):
// ============================================================
// import { createClient } from "@/lib/supabase";
// import { Session, User } from "@supabase/supabase-js";
// import { useRouter } from "next/navigation";
//
// export default function AuthProvider({ children }) {
//   const [user, setUser] = useState(null);
//   const [session, setSession] = useState(null);
//   const [loading, setLoading] = useState(true);
//   const router = useRouter();
//   const supabase = createClient();
//
//   useEffect(() => {
//     supabase.auth.getSession().then(({ data: { session } }) => {
//       setSession(session);
//       setUser(session?.user ?? null);
//       setLoading(false);
//       if (!session) router.push("/login");
//     });
//     const { data: { subscription } } = supabase.auth.onAuthStateChange(
//       (_event, session) => {
//         setSession(session);
//         setUser(session?.user ?? null);
//         if (!session) router.push("/login");
//       }
//     );
//     return () => subscription.unsubscribe();
//   }, []);
//
//   const signOut = async () => {
//     await supabase.auth.signOut();
//     router.push("/login");
//   };
//
//   return (
//     <AuthContext.Provider value={{ user, session, loading, signOut }}>
//       {children}
//     </AuthContext.Provider>
//   );
// }
