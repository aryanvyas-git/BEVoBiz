import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const MAX_CHART_ROWS = 30
const PRIMARY_COLOR = '#4f46e5'
const CHART_COLORS = ['#4f46e5', '#0ea5e9', '#10b981', '#f59e0b', '#f43f5e', '#8b5cf6', '#06b6d4', '#84cc16']
const TOOLTIP_STYLE = {
  borderRadius: 10,
  border: '1px solid #e5e7eb',
  boxShadow: '0 4px 16px rgba(16, 24, 40, 0.08)',
  fontSize: '0.85rem',
}

function isNumeric(value) {
  return typeof value === 'number' && Number.isFinite(value)
}

// Arbitrary queries return arbitrary shapes, so charting relies on a simple
// heuristic rather than any knowledge of what the question asked: the first
// non-numeric column becomes the category/label axis, the first numeric
// column becomes the value axis. If either is missing (e.g. a single
// aggregate number with no label column) there's nothing sensible to plot.
function pickAxes(columns, sampleRow) {
  let labelColumn = null
  let valueColumn = null

  for (const col of columns) {
    const value = sampleRow[col]
    if (valueColumn === null && isNumeric(value)) {
      valueColumn = col
    } else if (labelColumn === null && !isNumeric(value)) {
      labelColumn = col
    }
  }

  if (!labelColumn || !valueColumn) return null
  return { labelColumn, valueColumn }
}

export default function NlqChart({ columns, rows, type }) {
  if (!rows || rows.length === 0) {
    return <p className="muted-text">No data to chart.</p>
  }

  const axes = pickAxes(columns, rows[0])

  if (!axes) {
    return (
      <p className="muted-text">
        This answer is best viewed as text/table — it doesn't have a category and a number to plot.
      </p>
    )
  }

  const data = rows.slice(0, MAX_CHART_ROWS).map((row) => ({
    label: String(row[axes.labelColumn]),
    value: row[axes.valueColumn],
  }))
  const truncated = rows.length > MAX_CHART_ROWS

  return (
    <div>
      <ResponsiveContainer width="100%" height={320}>
        {type === 'bar' ? (
          <BarChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 40 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eef0f5" />
            <XAxis
              dataKey="label"
              angle={-30}
              textAnchor="end"
              interval={0}
              height={60}
              tick={{ fontSize: 12, fill: '#667085' }}
            />
            <YAxis tick={{ fontSize: 12, fill: '#667085' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: '#f5f6fb' }} />
            <Bar dataKey="value" fill={PRIMARY_COLOR} radius={[6, 6, 0, 0]} />
          </BarChart>
        ) : (
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="label" outerRadius={110} label>
              {data.map((_, i) => (
                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: '0.85rem' }} />
          </PieChart>
        )}
      </ResponsiveContainer>
      {truncated && (
        <p className="muted-text">
          Showing the first {MAX_CHART_ROWS} of {rows.length} rows.
        </p>
      )}
    </div>
  )
}
