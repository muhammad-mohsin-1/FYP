import React from 'react'
import { Routes, Route, Navigate, Link, useNavigate, useLocation } from 'react-router-dom'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Zones from './pages/Zones.jsx'
import Incidents from './pages/Incidents.jsx'
import Analytics from './pages/Analytics.jsx'
import Reports from './pages/Reports.jsx'

function Navbar() {
  const nav = useNavigate()
  const loc = useLocation()
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  if (!user) return null
  const logout = () => {
    localStorage.removeItem('token'); localStorage.removeItem('user')
    nav('/login')
  }
  const link = (to, label) => (
    <Link key={to} to={to} className={loc.pathname === to ? 'active' : ''}>{label}</Link>
  )
  return (
    <nav className="navbar">
      <strong>🛡️ ZoneGuard AI</strong>
      {link('/dashboard', 'Live Monitor')}
      {link('/incidents', 'Incidents')}
      {link('/analytics', 'Analytics')}
      {link('/reports', 'Reports')}
      {user.role === 'admin' && link('/zones', 'Zones')}
      <span className="spacer" />
      <span>{user.username} ({user.role})</span>
      <button className="btn btn-danger" onClick={logout}>Logout</button>
    </nav>
  )
}

function Protected({ children, adminOnly }) {
  const user = JSON.parse(localStorage.getItem('user') || 'null')
  if (!user) return <Navigate to="/login" />
  if (adminOnly && user.role !== 'admin') return <Navigate to="/dashboard" />
  return children
}

export default function App() {
  return (
    <>
      <Navbar />
      <div className="container">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/dashboard" element={<Protected><Dashboard /></Protected>} />
          <Route path="/incidents" element={<Protected><Incidents /></Protected>} />
          <Route path="/analytics" element={<Protected><Analytics /></Protected>} />
          <Route path="/reports" element={<Protected><Reports /></Protected>} />
          <Route path="/zones" element={<Protected adminOnly><Zones /></Protected>} />
          <Route path="/" element={<Navigate to="/dashboard" />} />
        </Routes>
      </div>
    </>
  )
}
