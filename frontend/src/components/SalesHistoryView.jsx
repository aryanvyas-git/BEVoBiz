import { useEffect, useState } from 'react'
import { listSales } from '../api/sales'

export default function SalesHistoryView({ refreshKey }) {
  const [sales, setSales] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function fetchSales() {
      setLoading(true)
      setError('')
      try {
        const data = await listSales()
        if (!cancelled) setSales(data)
      } catch {
        if (!cancelled) setError('Could not load sales history. Please try again.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    fetchSales()
    return () => {
      cancelled = true
    }
  }, [refreshKey])

  if (loading) {
    return <p className="muted-text">Loading sales…</p>
  }

  if (error) {
    return <p className="error-text">{error}</p>
  }

  if (sales.length === 0) {
    return (
      <div className="empty-state">
        <p>No sales yet — record your first one from the inventory tab.</p>
      </div>
    )
  }

  return (
    <table className="products-table">
      <thead>
        <tr>
          <th>Product</th>
          <th>Quantity</th>
          <th>Unit selling price</th>
          <th>Line total</th>
          <th>Line profit</th>
          <th>Sold at</th>
        </tr>
      </thead>
      <tbody>
        {sales.map((sale) => (
          <tr key={sale.id}>
            <td>{sale.product_name}</td>
            <td>{sale.quantity}</td>
            <td>${Number(sale.unit_selling_price).toFixed(2)}</td>
            <td>${Number(sale.line_total).toFixed(2)}</td>
            <td>${Number(sale.line_profit).toFixed(2)}</td>
            <td>{new Date(sale.sold_at).toLocaleString()}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
