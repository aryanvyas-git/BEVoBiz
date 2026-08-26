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
const PRIMARY_COLOR = '#ea6a42'
const CHART_COLORS = ['#ea6a42', '#e8a23f', '#dc4b3f', '#4c9a8f', '#b5657a', '#f0c14b', '#a85c32', '#7ea172']
const TOOLTIP_STYLE = {
  borderRadius: 12,
  border: '1px solid #f1e2d1',
  boxShadow: '0 8px 24px rgba(61, 46, 34, 0.12)',
  fontSize: '0.85rem',
  fontFamily: 'Nunito, sans-serif',
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
    return <p className="muted-text">📊 No data to chart.</p>
  }

  const axes = pickAxes(columns, rows[0])

  if (!axes) {
    return (
      <p className="muted-text">
        💡 This answer is best viewed as text/table — it doesn't have a category and a number to plot.
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
            <CartesianGrid strokeDasharray="3 3" stroke="#f1e2d1" />
            <XAxis
              dataKey="label"
              angle={-30}
              textAnchor="end"
              interval={0}
              height={60}
              tick={{ fontSize: 12, fill: '#8a7461' }}
            />
            <YAxis tick={{ fontSize: 12, fill: '#8a7461' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: '#fff3ec' }} />
            <Bar
              dataKey="value"
              fill={PRIMARY_COLOR}
              radius={[8, 8, 0, 0]}
              animationDuration={700}
              animationEasing="ease-out"
            />
          </BarChart>
        ) : (
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="label"
              outerRadius={110}
              label
              animationDuration={700}
              animationEasing="ease-out"
            >
              {data.map((_, i) => (
                <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: '0.85rem', fontFamily: 'Nunito, sans-serif' }} />
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
