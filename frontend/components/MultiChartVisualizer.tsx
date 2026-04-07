"use client";
import React from "react";
import {
  BarChart, Bar,
  LineChart, Line,
  PieChart, Pie, Cell,
  AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";

interface MultiChartVisualizerProps {
  data: any[];
  chartType: string; // "bar" | "line" | "pie" | "area"
}

const COLORS = ["#A4DA30", "#00A3FF", "#FF6B6B", "#FFD93D", "#6BCB77", "#4D96FF"];

export default function MultiChartVisualizer({ data, chartType }: MultiChartVisualizerProps) {
  if (!data || data.length === 0) return null;

  const commonAxisProps = {
    stroke: "#D0DCE3",
    tick: { fill: "#D0DCE3", fontSize: 12 },
    axisLine: false,
    tickLine: false,
  };

  const tooltipStyle = {
    contentStyle: {
      backgroundColor: "#002855",
      border: "1px solid rgba(255,255,255,0.1)",
      borderRadius: "8px",
    },
    itemStyle: { color: "#A4DA30" },
  };

  const renderChart = () => {
    switch (chartType) {
      case "line":
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
            <XAxis dataKey="name" {...commonAxisProps} />
            <YAxis {...commonAxisProps} width={50} />
            <Tooltip {...tooltipStyle} />
            <Line
              type="monotone"
              dataKey="value"
              stroke="#A4DA30"
              strokeWidth={2}
              dot={{ fill: "#A4DA30", r: 4 }}
              activeDot={{ r: 6, fill: "#b5f532" }}
            />
          </LineChart>
        );

      case "pie":
        return (
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={4}
              dataKey="value"
              nameKey="name"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip {...tooltipStyle} />
            <Legend
              wrapperStyle={{ color: "#D0DCE3", fontSize: "12px" }}
            />
          </PieChart>
        );

      case "area":
        return (
          <AreaChart data={data}>
            <defs>
              <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#A4DA30" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#A4DA30" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
            <XAxis dataKey="name" {...commonAxisProps} />
            <YAxis {...commonAxisProps} width={50} />
            <Tooltip {...tooltipStyle} />
            <Area
              type="monotone"
              dataKey="value"
              stroke="#A4DA30"
              fill="url(#areaGradient)"
              strokeWidth={2}
            />
          </AreaChart>
        );

      case "bar":
      default:
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#ffffff1a" vertical={false} />
            <XAxis dataKey="name" {...commonAxisProps} />
            <YAxis {...commonAxisProps} width={50} />
            <Tooltip cursor={{ fill: "rgba(255,255,255,0.05)" }} {...tooltipStyle} />
            <Bar dataKey="value" fill="#A4DA30" radius={[4, 4, 0, 0]} />
          </BarChart>
        );
    }
  };

  return (
    <div className="w-full h-64 mt-4 glass-panel rounded-xl p-4 transition-all duration-300">
      <h3 className="text-accent text-xs font-semibold mb-2 uppercase tracking-wider">
        Análisis Financiero
      </h3>
      <ResponsiveContainer width="100%" height="85%">
        {renderChart()}
      </ResponsiveContainer>
    </div>
  );
}
