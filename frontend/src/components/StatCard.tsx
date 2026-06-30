import { remainingColor } from "../theme";
import type { ReactNode } from "react";

interface StatCardProps {
  label: ReactNode;
  value: number;
  /** When true, color the value green/red based on sign (like Remaining columns). */
  colorBySign?: boolean;
}

/** Format a number as PHP currency, matching the desktop app. */
export function peso(value: number): string {
  return new Intl.NumberFormat("en-PH", {
    style: "currency",
    currency: "PHP",
    minimumFractionDigits: 2,
  }).format(value);
}

/** Dashboard summary tile — mirrors the desktop StatCard. */
export default function StatCard({ label, value, colorBySign }: StatCardProps) {
  const style = colorBySign ? { color: remainingColor(value) } : undefined;
  return (
    <div className="stat-card">
      <div className="label">{label}</div>
      <div className="value" style={style}>
        {peso(value)}
      </div>
    </div>
  );
}
