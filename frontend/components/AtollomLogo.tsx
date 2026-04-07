"use client";
import React from "react";

interface AtollomLogoProps {
  size?: number;
  className?: string;
  glowIntensity?: "none" | "subtle" | "medium" | "strong";
}

/**
 * Logo atómico de Atollom AI — 3 órbitas elípticas entrelazadas
 * Recrea fielmente el isotipo de la marca.
 */
export default function AtollomLogo({
  size = 32,
  className = "",
  glowIntensity = "subtle",
}: AtollomLogoProps) {
  const glowFilter = glowIntensity !== "none" ? `url(#atollom-glow-${glowIntensity})` : undefined;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="Atollom AI Logo"
    >
      <defs>
        {/* Glow filters */}
        <filter id="atollom-glow-subtle" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="1.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="atollom-glow-medium" x="-30%" y="-30%" width="160%" height="160%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        <filter id="atollom-glow-strong" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      <g filter={glowFilter}>
        {/* 3 órbitas elípticas rotadas a 0°, 60° y 120° */}
        {/* Órbita 1 — vertical (0° rotation) */}
        <ellipse
          cx="50"
          cy="50"
          rx="18"
          ry="42"
          stroke="currentColor"
          strokeWidth="5.5"
          strokeLinecap="round"
          fill="none"
          transform="rotate(0 50 50)"
        />
        {/* Órbita 2 — rotada 60° */}
        <ellipse
          cx="50"
          cy="50"
          rx="18"
          ry="42"
          stroke="currentColor"
          strokeWidth="5.5"
          strokeLinecap="round"
          fill="none"
          transform="rotate(60 50 50)"
        />
        {/* Órbita 3 — rotada 120° */}
        <ellipse
          cx="50"
          cy="50"
          rx="18"
          ry="42"
          stroke="currentColor"
          strokeWidth="5.5"
          strokeLinecap="round"
          fill="none"
          transform="rotate(120 50 50)"
        />
      </g>
    </svg>
  );
}
