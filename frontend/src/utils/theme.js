// Chart libraries (recharts) set colors as raw SVG attributes rather than
// through the CSS cascade, so `var(--color-*)` custom properties don't
// resolve there — these mirror the palette in index.css as literal hex
// values for chart use only. Keep the two in sync when re-theming.
export const CHART_PRIMARY = '#7c5cfa'
export const CHART_PRIMARY_LIGHT = '#f1edfe'
export const CHART_COLORS = [
  '#7c5cfa',
  '#ea6a42',
  '#2f9e5c',
  '#e8a23f',
  '#4c9a8f',
  '#dc4b3f',
  '#b5657a',
  '#5f3fe0',
]
export const CHART_GRID = '#e6e3ef'
export const CHART_MUTED_TEXT = '#6f6a82'
export const CHART_TOOLTIP_BORDER = '#e6e3ef'
