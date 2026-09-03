export function formatCurrency(value) {
  const n = Number(value) || 0
  return n.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
}

export function formatNumber(value) {
  const n = Number(value) || 0
  return n.toLocaleString('en-US')
}

export function formatShortDate(dateStr) {
  const d = new Date(`${dateStr}T00:00:00`)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
