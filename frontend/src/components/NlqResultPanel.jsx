import { useState } from 'react'
import NlqChart from './NlqChart'

const VIEWS = [
  { key: 'table', label: 'Table' },
  { key: 'bar', label: 'Bar chart' },
  { key: 'pie', label: 'Pie chart' },
]

export default function NlqResultPanel({ result }) {
  const [view, setView] = useState('table')
  const [sqlOpen, setSqlOpen] = useState(false)

  if (!result.executed) {
    return (
      <div className="nlq-result">
        <p className="error-text">
          {result.error || 'Something went wrong answering that question.'}
        </p>
      </div>
    )
  }

  const { answer, rows, columns, generated_sql: generatedSql } = result

  return (
    <div className="nlq-result">
      {answer && (
        <div className="nlq-answer-card">
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            style={{ color: 'var(--color-primary)', flexShrink: 0, marginTop: '2px' }}
          >
            <path d="M12 3l1.9 4.6L18.5 9.5l-4.6 1.9L12 16l-1.9-4.6L5.5 9.5l4.6-1.9L12 3z" />
          </svg>
          <p className="nlq-answer">{answer}</p>
        </div>
      )}

      <div className="tab-bar nlq-view-toggle">
        {VIEWS.map((v) => (
          <button
            key={v.key}
            type="button"
            className={`tab-btn ${view === v.key ? 'active' : ''}`}
            onClick={() => setView(v.key)}
          >
            {v.label}
          </button>
        ))}
      </div>

      <div className="nlq-view-body">
        {view === 'table' ? (
          rows.length === 0 ? (
            <p className="muted-text">🔍 Your query ran but returned no data.</p>
          ) : (
            <div className="nlq-table-wrap">
              <table className="products-table">
                <thead>
                  <tr>
                    {columns.map((col) => (
                      <th key={col}>{col}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row, i) => (
                    <tr key={i}>
                      {columns.map((col) => (
                        <td key={col}>
                          {row[col] === null || row[col] === undefined ? '—' : String(row[col])}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )
        ) : (
          <NlqChart columns={columns} rows={rows} type={view} />
        )}
      </div>

      {generatedSql && (
        <div className="nlq-sql-detail">
          <button type="button" className="btn-link" onClick={() => setSqlOpen((o) => !o)}>
            {sqlOpen ? 'Hide query' : 'Show query'}
          </button>
          {sqlOpen && <pre className="nlq-sql-code">{generatedSql}</pre>}
        </div>
      )}
    </div>
  )
}
