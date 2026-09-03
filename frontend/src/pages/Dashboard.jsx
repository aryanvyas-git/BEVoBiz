import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Sidebar from '../components/Sidebar'
import DashboardHome from '../components/DashboardHome'
import InventoryView from '../components/InventoryView'
import SalesHistoryView from '../components/SalesHistoryView'
import NlqSearch from '../components/NlqSearch'

const VIEW_TITLES = {
  dashboard: 'Dashboard',
  inventory: 'Inventory',
  sales: 'Sales History',
}

export default function Dashboard() {
  const { business, logout } = useAuth()
  const navigate = useNavigate()

  const [view, setView] = useState('dashboard')
  const [salesRefreshKey, setSalesRefreshKey] = useState(0)
  const [inventoryIntent, setInventoryIntent] = useState(null)

  function handleLogout() {
    logout()
    navigate('/login')
  }

  function handleNavigateToInventory(intent) {
    setInventoryIntent(intent)
    setView('inventory')
  }

  return (
    <div className="app-shell">
      <Sidebar activeView={view} onNavigate={setView} />

      <div className="app-main">
        <header className="app-topbar">
          <h1 className="app-topbar-title">
            {business ? business.name : '…'}
            <span className="app-topbar-subtitle">· {VIEW_TITLES[view]}</span>
          </h1>
          <button className="btn-secondary" onClick={handleLogout}>
            Logout
          </button>
        </header>

        <div className="app-content">
          <NlqSearch />

          {view === 'dashboard' && (
            <DashboardHome onNavigateToInventory={handleNavigateToInventory} />
          )}
          {view === 'inventory' && (
            <InventoryView
              intent={inventoryIntent}
              onIntentConsumed={() => setInventoryIntent(null)}
              onSaleRecorded={() => setSalesRefreshKey((k) => k + 1)}
            />
          )}
          {view === 'sales' && <SalesHistoryView refreshKey={salesRefreshKey} />}
        </div>
      </div>
    </div>
  )
}
