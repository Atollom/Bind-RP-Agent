"use client";
import React, { useState, useEffect, useCallback } from "react";
import { Download, FileSpreadsheet, FileText, Search, RefreshCw, Loader2 } from "lucide-react";
import { useAuth } from "./AuthProvider";
import MultiChartVisualizer from "./MultiChartVisualizer";

interface ModuleViewProps {
  moduleId: string;
  title: string;
  query: string;
  chartType?: string;
}

const MODULE_COLUMNS: Record<string, string[]> = {
  VENTAS:       ["Serie", "Folio", "Fecha", "Cliente", "Total", "Estado"],
  INVENTARIO:   ["Clave", "Descripcion", "Existencia", "Precio", "Unidad"],
  COMPRAS:      ["Folio", "Fecha", "Proveedor", "Total", "Estado"],
  CONTABILIDAD: ["Numero", "Nombre", "Tipo", "Saldo"],
  DIRECTORIO:   ["RFC", "RazonSocial", "Email", "Telefono", "Ciudad"],
};

export default function ModuleView({ moduleId, title, query, chartType = "bar" }: ModuleViewProps) {
  const { session } = useAuth();
  const [data, setData] = useState<any[]>([]);
  const [analysis, setAnalysis] = useState("");
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<"excel" | "pdf" | null>(null);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const token = session?.access_token;

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${apiUrl}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: query }),
      });
      const json = await res.json();
      setData(json?.response?.chartData || []);
      setAnalysis(json?.response?.content || "");
    } catch {
      setError("No se pudo cargar la información de Bind ERP.");
    } finally {
      setLoading(false);
    }
  }, [apiUrl, token, query]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const exportFile = async (format: "excel" | "pdf") => {
    if (!data.length) return;
    setExporting(format);
    try {
      const res = await fetch(`${apiUrl}/api/export/${format}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ title: `${title} — Atollom AI`, intent: moduleId, data, summary: analysis }),
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `atollom_${moduleId.toLowerCase()}_${Date.now()}.${format === "excel" ? "xlsx" : "pdf"}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      alert("Error al generar el reporte. Intenta de nuevo.");
    } finally {
      setExporting(null);
    }
  };

  // Filtrar filas por búsqueda
  const filteredData = data.filter(row =>
    !search || Object.values(row).some(v => String(v).toLowerCase().includes(search.toLowerCase()))
  );

  // Columnas a mostrar
  const preferredCols = MODULE_COLUMNS[moduleId] || [];
  const allKeys = data.length ? Object.keys(data[0]) : [];
  const displayCols = preferredCols.length
    ? allKeys.filter(k => preferredCols.some(p => k.toLowerCase().includes(p.toLowerCase()))).slice(0, 7)
    : allKeys.slice(0, 7);
  const cols = displayCols.length ? displayCols : allKeys.slice(0, 7);

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-6 pb-3 flex-shrink-0">
        <div>
          <h2 className="text-2xl font-bold text-textPrimary">{title}</h2>
          <p className="text-sm text-textPrimary/50 mt-0.5">Datos en tiempo real desde Bind ERP</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={fetchData} disabled={loading}
            className="p-2 rounded-lg text-textPrimary/50 hover:bg-white/5 transition-all disabled:opacity-30" title="Actualizar">
            <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
          </button>
          <button onClick={() => exportFile("excel")} disabled={!data.length || !!exporting}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm border border-green-500/30 text-green-400 hover:bg-green-500/10 transition-all disabled:opacity-30">
            {exporting === "excel" ? <Loader2 size={14} className="animate-spin" /> : <FileSpreadsheet size={14} />}
            Excel
          </button>
          <button onClick={() => exportFile("pdf")} disabled={!data.length || !!exporting}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm border border-red-500/30 text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-30">
            {exporting === "pdf" ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
            PDF
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 pb-6 space-y-4">
        {/* Análisis de Gemini */}
        {analysis && !loading && (
          <div className="glass-panel rounded-xl p-4 border-l-2 border-accent/50 text-sm text-textPrimary/80 leading-relaxed">
            {analysis}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-xl px-4 py-3">{error}</div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <Loader2 size={32} className="animate-spin text-accent mx-auto mb-3" />
              <p className="text-textPrimary/50 text-sm">Consultando Bind ERP...</p>
            </div>
          </div>
        )}

        {/* Gráfica */}
        {!loading && data.length > 0 && (
          <MultiChartVisualizer data={data.slice(0, 20)} chartType={chartType} />
        )}

        {/* Búsqueda + Tabla */}
        {!loading && data.length > 0 && (
          <>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-textPrimary/30" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Buscar en resultados..."
                className="w-full bg-background/60 border border-white/10 rounded-xl pl-9 pr-4 py-2.5 text-sm text-textPrimary placeholder:text-textPrimary/30 outline-none focus:border-accent/50 transition-all"
              />
            </div>

            <div className="rounded-xl border border-white/5 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-[#001C3E]/80">
                      {cols.map(col => (
                        <th key={col} className="px-4 py-3 text-left text-xs font-semibold text-textPrimary/60 uppercase tracking-wider whitespace-nowrap">
                          {col.replace(/([A-Z])/g, ' $1').trim()}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filteredData.slice(0, 100).map((row, i) => (
                      <tr key={i} className={`border-t border-white/5 hover:bg-white/3 transition-colors ${i % 2 === 0 ? "bg-white/1" : ""}`}>
                        {cols.map(col => (
                          <td key={col} className="px-4 py-2.5 text-textPrimary/80 whitespace-nowrap max-w-[200px] truncate">
                            {String(row[col] ?? "—")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="px-4 py-2 border-t border-white/5 text-xs text-textPrimary/30 flex justify-between">
                <span>{filteredData.length} registros{search ? " filtrados" : ""} de {data.length} total</span>
                {data.length > 100 && <span>Mostrando primeros 100</span>}
              </div>
            </div>
          </>
        )}

        {/* Sin datos */}
        {!loading && !error && data.length === 0 && (
          <div className="flex flex-col items-center justify-center py-20 text-textPrimary/30">
            <Download size={32} className="mb-3 opacity-30" />
            <p className="text-sm">No se encontraron registros en Bind ERP para este módulo.</p>
          </div>
        )}
      </div>
    </div>
  );
}
