/**
 * theme.ts — ported color palette from the desktop app (widgets.py COLORS).
 * Keep these identical so the web app matches the desktop look.
 */
export const COLORS = {
  bg:         "#1a1a2e",
  sidebar:    "#16213e",
  card:       "#0f3460",
  cardHover:  "#1a4a7a",
  accent:     "#e94560",
  accent2:    "#533483",
  green:      "#2ecc71",
  yellow:     "#f39c12",
  red:        "#e74c3c",
  text:       "#eaeaea",
  subtext:    "#a0a0b0",
  inputBg:    "#162447",
  border:     "#253460",
} as const;

export type ColorKey = keyof typeof COLORS;

/** Fund type labels (from funds_view.py FUND_TYPE_LABELS). */
export const FUND_TYPE_LABELS: Record<string, string> = {
  salary: "Salary",
  bonus:  "Bonus",
  espp:   "ESPP",
  other:  "Other",
};

/** Remaining color rule: green > 0, yellow = 0, red < 0. */
export function remainingColor(value: number): string {
  if (value > 0) return COLORS.green;
  if (value < 0) return COLORS.red;
  return COLORS.yellow;
}

/** Missing expense color: green = 0 (all accounted for), yellow > 0 (extra), red < 0 (deficit). */
export function missingColor(value: number): string {
  if (value === 0) return COLORS.green;
  if (value > 0) return COLORS.yellow;
  return COLORS.red;
}
