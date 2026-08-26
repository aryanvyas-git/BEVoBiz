import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import InventoryView from '../components/InventoryView'
import SalesHistoryView from '../components/SalesHistoryView'

export default function Dashboard() {
  const { business, logout } = useAuth()
  const navigate = useNavigate()

  const [activeTab, setActiveTab] = useState('inventory')
  const [salesRefreshKey, setSalesRefreshKey] = useState(0)

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="inventory-page">
      <header className="inventory-header">
        <h1>Welcome, {business ? business.name : '…'}</h1>
        <button className="btn-danger" onClick={handleLogout}>
          Logout
        </button>
      </header>

      <div className="tab-bar">
        <button
          className={`tab-btn ${activeTab === 'inventory' ? 'active' : ''}`}
          onClick={() => setActiveTab('inventory')}
        >
          Inventory
        </button>
        <button
          className={`tab-btn ${activeTab === 'sales' ? 'active' : ''}`}
          onClick={() => setActiveTab('sales')}
        >
          Sales history
        </button>
      </div>

      {activeTab === 'inventory' ? (
        <InventoryView onSaleRecorded={() => setSalesRefreshKey((k) => k + 1)} />
      ) : (
        <SalesHistoryView refreshKey={salesRefreshKey} />
      )}
    </div>
  )
}
