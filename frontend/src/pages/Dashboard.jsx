import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Dashboard() {
  const { business, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="dashboard">
      <h1>Welcome, {business ? business.name : '…'}</h1>
      <button onClick={handleLogout}>Logout</button>
    </div>
  )
}
