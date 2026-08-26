import { useState } from 'react'
import Modal from './Modal'
import { createSale } from '../api/sales'
import { getErrorMessage } from '../api/errors'

function toDatetimeLocalValue(date) {
  const pad = (n) => String(n).padStart(2, '0')
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  )
}

export default function RecordSaleModal({ product, onClose, onSuccess }) {
  const [quantity, setQuantity] = useState(1)
  const [soldAt, setSoldAt] = useState(() => toDatetimeLocalValue(new Date()))
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const parsedQuantity = Number(quantity)
  const validQuantity = Number.isFinite(parsedQuantity) && parsedQuantity > 0
  const exceedsStock = validQuantity && parsedQuantity > product.quantity_in_stock
  const runningTotal = validQuantity ? parsedQuantity * Number(product.selling_price) : 0
  const canSubmit = validQuantity && !exceedsStock && !submitting

  async function handleSubmit(e) {
    e.preventDefault()
    if (!canSubmit) return
    setError('')
    setSubmitting(true)
    try {
      const sale = await createSale({
        product_id: product.id,
        quantity: parsedQuantity,
        sold_at: new Date(soldAt).toISOString(),
      })
      onSuccess(sale)
    } catch (err) {
      setError(getErrorMessage(err, 'Could not record sale'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Modal title={`Record sale — ${product.name}`} onClose={onClose}>
      <form className="product-form" onSubmit={handleSubmit}>
        <p className="stock-available">
          Available in stock: <strong>{product.quantity_in_stock}</strong>
        </p>

        <label>
          Quantity
          <input
            type="number"
            min="1"
            step="1"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            required
          />
        </label>

        <label>
          Time of sale
          <input
            type="datetime-local"
            value={soldAt}
            onChange={(e) => setSoldAt(e.target.value)}
            required
          />
        </label>

        <div className="running-total">
          <span>Total</span>
          <strong>${runningTotal.toFixed(2)}</strong>
        </div>

        {exceedsStock && (
          <span className="error-text">Only {product.quantity_in_stock} in stock</span>
        )}
        {error && <span className="error-text">{error}</span>}

        <div className="product-form-actions">
          <button type="button" className="btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" disabled={!canSubmit}>
            {submitting ? 'Recording…' : 'Record sale'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
