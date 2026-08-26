import { useState } from 'react'
import { getErrorMessage } from '../api/errors'

export default function ProductForm({ initialProduct, onSubmit, onCancel }) {
  const [name, setName] = useState(initialProduct?.name ?? '')
  const [category, setCategory] = useState(initialProduct?.category ?? '')
  const [costPrice, setCostPrice] = useState(initialProduct?.cost_price ?? '')
  const [sellingPrice, setSellingPrice] = useState(initialProduct?.selling_price ?? '')
  const [quantityInStock, setQuantityInStock] = useState(
    initialProduct?.quantity_in_stock ?? 0,
  )
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await onSubmit({
        name,
        category: category || null,
        cost_price: costPrice,
        selling_price: sellingPrice,
        quantity_in_stock: Number(quantityInStock),
      })
    } catch (err) {
      setError(getErrorMessage(err, 'Something went wrong'))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="product-form" onSubmit={handleSubmit}>
      <label>
        Name
        <input value={name} onChange={(e) => setName(e.target.value)} required />
      </label>
      <label>
        Category
        <input value={category} onChange={(e) => setCategory(e.target.value)} />
      </label>
      <label>
        Cost price
        <input
          type="number"
          step="0.01"
          min="0"
          value={costPrice}
          onChange={(e) => setCostPrice(e.target.value)}
          required
        />
      </label>
      <label>
        Selling price
        <input
          type="number"
          step="0.01"
          min="0"
          value={sellingPrice}
          onChange={(e) => setSellingPrice(e.target.value)}
          required
        />
      </label>
      <label>
        Quantity in stock
        <input
          type="number"
          step="1"
          min="0"
          value={quantityInStock}
          onChange={(e) => setQuantityInStock(e.target.value)}
          required
        />
      </label>
      {error && <span className="error-text">{error}</span>}
      <div className="product-form-actions">
        <button type="button" className="btn-secondary" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" disabled={submitting}>
          {submitting ? 'Saving…' : 'Save'}
        </button>
      </div>
    </form>
  )
}
