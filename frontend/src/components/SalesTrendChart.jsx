import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatCurrency, formatShortDate } from '../utils/format'
import { CHART_GRID, CHART_MUTED_TEXT, CHART_PRIMARY, CHART_TOOLTIP_BORDER } from '../utils/theme'

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null
  const point = payload[0].payload
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-date">{formatShortDate(label)}</div>
      <div className="chart-tooltip-row">
        <span>Revenue</span>
        <strong>{formatCurrency(point.revenue)}</strong>
      </div>
      <div className="chart-tooltip-row">
        <span>Units sold</span>
        <strong>{point.units}</strong>
      </div>
    </div>
  )
}

export default function SalesTrendChart({ data }) {
  const hasAnySales = data.some((d) => Number(d.revenue) > 0)

  if (!hasAnySales) {
    return <p className="muted-text">📈 No sales recorded in the last 30 days yet.</p>
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="salesRevenueFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={CHART_PRIMARY} stopOpacity={0.35} />
            <stop offset="100%" stopColor={CHART_PRIMARY} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_GRID} vertical={false} />
        <XAxis
          dataKey="date"
          tickFormatter={formatShortDate}
          tick={{ fontSize: 11, fill: CHART_MUTED_TEXT }}
          interval={Math.ceil(data.length / 8) - 1}
          axisLine={{ stroke: CHART_TOOLTIP_BORDER }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: CHART_MUTED_TEXT }}
          axisLine={false}
          tickLine={false}
          width={56}
          tickFormatter={(v) => `$${v}`}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="revenue"
          stroke={CHART_PRIMARY}
          strokeWidth={2.5}
          fill="url(#salesRevenueFill)"
          animationDuration={700}
          animationEasing="ease-out"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
