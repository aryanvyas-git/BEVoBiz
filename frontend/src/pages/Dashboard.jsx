import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { createProduct, deleteProduct, listProducts, updateProduct } from '../api/products'
import Modal from '../components/Modal'
import ProductForm from '../components/ProductForm'
import ConfirmDialog from '../components/ConfirmDialog'

export default function Dashboard() {
  const { business, logout } = useAuth()
  const navigate = useNavigate()

  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')

  const [formOpen, setFormOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState(null)
  const [deletingProduct, setDeletingProduct] = useState(null)
  const [deleting, setDeleting] = useState(false)

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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handleLogout() {
    logout()
    navigate('/login')
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

  return (
    <div className="inventory-page">
      <header className="inventory-header">
        <h1>Welcome, {business ? business.name : '…'}</h1>
        <button className="btn-danger" onClick={handleLogout}>
          Logout
        </button>
      </header>

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

      {error && <p className="error-text">{error}</p>}

      {loading ? (
        <p className="muted-text">Loading products…</p>
      ) : products.length === 0 ? (
        <div className="empty-state">
          <p>No products yet — add your first one.</p>
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
    </div>
  )
}
