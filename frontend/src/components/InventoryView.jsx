import { useEffect, useRef, useState } from 'react'
import { createProduct, deleteProduct, listProducts, updateProduct } from '../api/products'
import Modal from './Modal'
import ProductForm from './ProductForm'
import ConfirmDialog from './ConfirmDialog'
import RecordSaleModal from './RecordSaleModal'

export default function InventoryView({ onSaleRecorded }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  const [formOpen, setFormOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  const [deletingProduct, setDeletingProduct] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [sellingProduct, setSellingProduct] = useState(null)
  const [successMessage, setSuccessMessage] = useState('')
  const successTimerRef = useRef(null)

  async function fetchProducts(searchTerm = search) {
    setLoading(true)
    setError('')
    try {
      const data = await listProducts(searchTerm ? { search: searchTerm } : {})
      setProducts(data)
    } catch {
      setError('Could not load products. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProducts()
    return () => clearTimeout(successTimerRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function showSuccess(message) {
    setSuccessMessage(message)
    clearTimeout(successTimerRef.current)
    successTimerRef.current = setTimeout(() => setSuccessMessage(''), 2500)
  }

  function openAddForm() {
    setEditingProduct(null)
    setFormOpen(true)
  }

  function openEditForm(product) {
    setEditingProduct(product)
    setFormOpen(true)
  }

  async function handleFormSubmit(values) {
    if (editingProduct) {
      await updateProduct(editingProduct.id, values)
    } else {
      await createProduct(values)
    }
    setFormOpen(false)
    setEditingProduct(null)
    await fetchProducts()
  }

  async function handleDeleteConfirm() {
    setDeleting(true)
    try {
      await deleteProduct(deletingProduct.id)
      setProducts((prev) => prev.filter((p) => p.id !== deletingProduct.id))
      setDeletingProduct(null)
    } catch {
      setError('Could not delete product. Please try again.')
    } finally {
      setDeleting(false)
    }
  }

  function handleSearchSubmit(e) {
    e.preventDefault()
    fetchProducts(search)
  }

  function handleClearSearch() {
    setSearch('')
    fetchProducts('')
  }

  function handleSaleSuccess(sale) {
    setProducts((prev) =>
      prev.map((p) =>
        p.id === sale.product_id
          ? { ...p, quantity_in_stock: p.quantity_in_stock - sale.quantity }
          : p,
      ),
    )
    setSellingProduct(null)
    showSuccess(`Sale recorded: ${sale.quantity} × ${sale.product_name}`)
    onSaleRecorded?.()
  }

  return (
    <div>
      <div className="inventory-toolbar">
        <form onSubmit={handleSearchSubmit} className="search-form">
          <div className="search-input-wrap">
            <input
              type="text"
              placeholder="Search by name…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
            {search && (
              <button
                type="button"
                className="search-clear-btn"
                onClick={handleClearSearch}
                aria-label="Clear search"
              >
                ×
              </button>
            )}
          </div>
          <button type="submit" className="btn-secondary">
            Search
          </button>
        </form>
        <button onClick={openAddForm}>Add product</button>
      </div>

      {successMessage && <p className="success-text">{successMessage}</p>}
      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <p className="muted-text">Loading products…</p>
      ) : products.length === 0 ? (
        <div className="empty-state">
          <p>📦 No products yet — add your first one.</p>
          <button onClick={openAddForm}>Add product</button>
        </div>
      ) : (
        <table className="products-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Category</th>
              <th>Cost price</th>
              <th>Selling price</th>
              <th>Profit / unit</th>
              <th>Qty in stock</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}>
                <td>{product.name}</td>
                <td>{product.category || '—'}</td>
                <td>${Number(product.cost_price).toFixed(2)}</td>
                <td>${Number(product.selling_price).toFixed(2)}</td>
                <td>${Number(product.profit_per_unit).toFixed(2)}</td>
                <td>{product.quantity_in_stock}</td>
                <td className="row-actions">
                  <button className="btn-link" onClick={() => setSellingProduct(product)}>
                    Record sale
                  </button>
                  <button className="btn-link" onClick={() => openEditForm(product)}>
                    Edit
                  </button>
                  <button className="btn-link btn-link-danger" onClick={() => setDeletingProduct(product)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {formOpen && (
        <Modal
          title={editingProduct ? 'Edit product' : 'Add product'}
          onClose={() => {
            setFormOpen(false)
            setEditingProduct(null)
          }}
        >
          <ProductForm
            initialProduct={editingProduct}
            onSubmit={handleFormSubmit}
            onCancel={() => {
              setFormOpen(false)
              setEditingProduct(null)
            }}
          />
        </Modal>
      )}

      {deletingProduct && (
        <ConfirmDialog
          title="Delete product"
          message={`Are you sure you want to delete "${deletingProduct.name}"? This cannot be undone.`}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setDeletingProduct(null)}
          confirming={deleting}
        />
      )}

      {sellingProduct && (
        <RecordSaleModal
          product={sellingProduct}
          onClose={() => setSellingProduct(null)}
          onSuccess={handleSaleSuccess}
        />
      )}
    </div>
  )
}
