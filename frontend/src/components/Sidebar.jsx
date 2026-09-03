const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', icon: 'grid' },
  { key: 'inventory', label: 'Inventory', icon: 'box' },
  { key: 'sales', label: 'Sales History', icon: 'receipt' },
]

const SOON_ITEMS = [
  { label: 'Suppliers', icon: 'truck' },
  { label: 'Purchase Orders', icon: 'clipboard' },
  { label: 'Warehouses & Locations', icon: 'building' },
  { label: 'Analytics', icon: 'chart' },
]

const ICONS = {
  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  box: (
    <>
      <path d="M21 8l-9-5-9 5 9 5 9-5z" />
      <path d="M3 8v8l9 5 9-5V8" />
      <path d="M12 13v8" />
    </>
  ),
  receipt: (
    <>
      <path d="M5 3h14v18l-3-2-2 2-2-2-2 2-2-2-3 2V3z" />
      <path d="M8 8h8M8 12h8M8 16h5" />
    </>
  ),
  truck: (
    <>
      <path d="M3 7h11v9H3z" />
      <path d="M14 10h4l3 3v3h-7z" />
      <circle cx="7" cy="18" r="1.7" />
      <circle cx="17.5" cy="18" r="1.7" />
    </>
  ),
  clipboard: (
    <>
      <rect x="6" y="4" width="12" height="17" rx="1.5" />
      <path d="M9 4V3a1 1 0 011-1h4a1 1 0 011 1v1" />
      <path d="M9 11h6M9 15h6" />
    </>
  ),
  building: (
    <>
      <rect x="4" y="3" width="10" height="18" />
      <rect x="14" y="9" width="6" height="12" />
      <path d="M7 7h1M10 7h1M7 11h1M10 11h1M7 15h1M10 15h1" />
    </>
  ),
  chart: (
    <>
      <path d="M4 20V10M12 20V4M20 20v-7" />
    </>
  ),
}

function NavIcon({ name }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {ICONS[name]}
    </svg>
  )
}

export default function Sidebar({ activeView, onNavigate }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <span className="brand-mark">B</span>
        <span className="brand-name">BEVoBIZ</span>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.key}
            type="button"
            className={`sidebar-nav-item ${activeView === item.key ? 'active' : ''}`}
            onClick={() => onNavigate(item.key)}
          >
            <NavIcon name={item.icon} />
            {item.label}
          </button>
        ))}
      </nav>

      <div className="sidebar-divider">
        <span>Coming soon</span>
      </div>

      <nav className="sidebar-nav">
        {SOON_ITEMS.map((item) => (
          <button
            key={item.label}
            type="button"
            className="sidebar-nav-item sidebar-nav-item-soon"
            disabled
            aria-disabled="true"
            title="Coming soon"
          >
            <NavIcon name={item.icon} />
            {item.label}
            <span className="soon-badge">Soon</span>
          </button>
        ))}
      </nav>
    </aside>
  )
}
