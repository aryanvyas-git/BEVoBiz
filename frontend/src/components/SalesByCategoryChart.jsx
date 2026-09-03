import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { formatCurrency } from '../utils/format'
import { CHART_COLORS, CHART_TOOLTIP_BORDER } from '../utils/theme'

const TOOLTIP_STYLE = {
  borderRadius: 12,
  border: `1px solid ${CHART_TOOLTIP_BORDER}`,
  boxShadow: '0 8px 24px rgba(43, 36, 56, 0.14)',
  fontSize: '0.85rem',
  fontFamily: 'Nunito, sans-serif',
}

export default function SalesByCategoryChart({ data }) {
  if (!data || data.length === 0) {
    return <p className="muted-text">🥧 No categorized sales yet.</p>
  }

  const chartData = data.map((d) => ({ name: d.category, value: Number(d.revenue) }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={chartData}
          dataKey="value"
          nameKey="name"
          innerRadius={44}
          outerRadius={78}
          paddingAngle={2}
          animationDuration={700}
          animationEasing="ease-out"
        >
          {chartData.map((_, i) => (
            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={TOOLTIP_STYLE}
          formatter={(value) => formatCurrency(value)}
        />
        <Legend wrapperStyle={{ fontSize: '0.78rem', fontFamily: 'Nunito, sans-serif' }} />
      </PieChart>
    </ResponsiveContainer>
  )
}
