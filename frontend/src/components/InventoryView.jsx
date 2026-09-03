import { useEffect, useRef, useState } from 'react'
import { createProduct, deleteProduct, listProducts, updateProduct } from '../api/products'
import Modal from './Modal'
import ProductForm from './ProductForm'
import ConfirmDialog from './ConfirmDialog'
import RecordSaleModal from './RecordSaleModal'

const STATUS_FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'in_stock', label: 'In Stock' },
  { key: 'low_stock', label: 'Low Stock' },
  { key: 'out_of_stock', label: 'Out of Stock' },
]

const STATUS_LABELS = {
  in_stock: 'In Stock',
  low_stock: 'Low Stock',
  out_of_stock: 'Out of Stock',
}

function StockBar({ product }) {
  const scale = Math.max(product.reorder_level * 3, 10)
  const pct = Math.min(100, Math.round((product.quantity_in_stock / scale) * 100))
  return (
    <div className="stock-bar" title={`${product.quantity_in_stock} in stock, reorder at ${product.reorder_level}`}>
      <div className={`stock-bar-fill stock-bar-fill-${product.stock_status}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export default function InventoryView({ onSaleRecorded, intent, onIntentConsumed }) {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

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
      return data
    } catch {
      setError('Could not load products. Please try again.')
      return []
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchProducts()
    return () => clearTimeout(successTimerRef.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!intent) return

    if (intent.filter) {
      setStatusFilter(intent.filter)
    }

    if (intent.editProductId) {
      if (products.length === 0) return // wait for the initial fetch to land
      const product = products.find((p) => p.id === intent.editProductId)
      if (product) {
        openEditForm(product)
      }
    }

    onIntentConsumed?.()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intent, products])

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
          ? {
              ...p,
              quantity_in_stock: p.quantity_in_stock - sale.quantity,
              stock_status:
                p.quantity_in_stock - sale.quantity === 0
                  ? 'out_of_stock'
                  : p.quantity_in_stock - sale.quantity <= p.reorder_level
                    ? 'low_stock'
                    : 'in_stock',
            }
          : p,
      ),
    )
    setSellingProduct(null)
    showSuccess(`Sale recorded: ${sale.quantity} × ${sale.product_name}`)
    onSaleRecorded?.()
  }

  const filteredProducts =
    statusFilter === 'all' ? products : products.filter((p) => p.stock_status === statusFilter)

  const statusCounts = products.reduce(
    (acc, p) => {
      acc[p.stock_status] = (acc[p.stock_status] || 0) + 1
      return acc
    },
    { in_stock: 0, low_stock: 0, out_of_stock: 0 },
  )

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

      <div className="tab-bar inventory-filter-bar">
        {STATUS_FILTERS.map((f) => (
          <button
            key={f.key}
            type="button"
            className={`tab-btn ${statusFilter === f.key ? 'active' : ''}`}
            onClick={() => setStatusFilter(f.key)}
          >
            {f.label}
            {f.key !== 'all' && statusCounts[f.key] > 0 && (
              <span className="tab-btn-count">{statusCounts[f.key]}</span>
            )}
          </button>
        ))}
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
      ) : filteredProducts.length === 0 ? (
        <div className="empty-state">
          <p>🔍 No products match this filter.</p>
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
              <th>Stock</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.map((product) => (
              <tr key={product.id}>
                <td>{product.name}</td>
                <td>{product.category || '—'}</td>
                <td>${Number(product.cost_price).toFixed(2)}</td>
                <td>${Number(product.selling_price).toFixed(2)}</td>
                <td>${Number(product.profit_per_unit).toFixed(2)}</td>
                <td>
                  <div className="stock-cell">
                    <span>{product.quantity_in_stock}</span>
                    <StockBar product={product} />
                  </div>
                </td>
                <td>
                  <span className={`status-pill status-pill-${product.stock_status}`}>
                    {STATUS_LABELS[product.stock_status]}
                  </span>
                </td>
                <td>
                  <div className="row-actions">
                    <button className="btn-link" onClick={() => setSellingProduct(product)}>
                      Record sale
                    </button>
                    <button className="btn-link" onClick={() => openEditForm(product)}>
                      Edit
                    </button>
                    <button className="btn-link btn-link-danger" onClick={() => setDeletingProduct(product)}>
                      Delete
                    </button>
                  </div>
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
