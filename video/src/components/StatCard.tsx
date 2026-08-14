import React from "react";
import { theme } from "../theme";

export const StatCard: React.FC<{
  value: string;
  unit?: string;
  label: string;
  accent?: string;
}> = ({ value, unit, label, accent = theme.color.shamrock }) => (
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: 8,
      border: `2px solid ${theme.color.paper}55`,
      padding: "20px 28px",
      minWidth: 260,
    }}
  >
    <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
      <span
        style={{
          fontFamily: theme.font.computed,
          fontSize: 72,
          lineHeight: 1,
          color: accent,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {value}
      </span>
      {unit ? (
        <span
          style={{
            fontFamily: theme.font.computed,
            fontSize: 36,
            color: accent,
          }}
        >
          {unit}
        </span>
      ) : null}
    </div>
    <span
      style={{
        fontFamily: theme.font.chrome,
        fontSize: 20,
        color: theme.color.paper,
        letterSpacing: "0.04em",
      }}
    >
      {label}
    </span>
  </div>
);
