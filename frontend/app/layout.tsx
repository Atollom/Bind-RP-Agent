import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: '--font-inter' });

export const metadata: Metadata = {
  title: "Atollom AI Dashboard",
  description: "Plataforma B2B para inteligencia financiera y operativa impulsada por IA",
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
  }
};

export const viewport: Viewport = {
  themeColor: "#001C3E",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" className={inter.variable}>
      <body className="bg-background text-textPrimary antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
