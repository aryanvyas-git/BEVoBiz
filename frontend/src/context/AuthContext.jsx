import { createContext, useContext, useEffect, useState } from 'react'
import apiClient from '../api/axios'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))
  const [user, setUser] = useState(null)
  const [business, setBusiness] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadMe() {
      if (!token) {
        setLoading(false)
        return
      }
      try {
        const res = await apiClient.get('/auth/me')
        setUser(res.data.user)
        setBusiness(res.data.business)
      } catch {
        localStorage.removeItem('token')
        setToken(null)
        setUser(null)
        setBusiness(null)
      } finally {
        setLoading(false)
      }
    }
    loadMe()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token])

  async function signup(businessName, email, password) {
    const res = await apiClient.post('/auth/signup', {
      business_name: businessName,
      email,
      password,
    })
    localStorage.setItem('token', res.data.access_token)
    setToken(res.data.access_token)
  }

  async function login(email, password) {
    const res = await apiClient.post('/auth/login', { email, password })
    localStorage.setItem('token', res.data.access_token)
    setToken(res.data.access_token)
  }

  function logout() {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
    setBusiness(null)
  }

  const value = {
    token,
    user,
    business,
    loading,
    isAuthenticated: Boolean(token),
    signup,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return ctx
}
