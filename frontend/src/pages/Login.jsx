import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import client from '../api/client.js'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const nav = useNavigate()

  const submit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      // FastAPI OAuth2 password flow expects form-encoded body
      const body = new URLSearchParams({ username, password })
      const res = await client.post('/auth/login', body, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('user', JSON.stringify({ username: res.data.username, role: res.data.role }))
      nav('/dashboard')
    } catch {
      setError('Invalid username or password')
    }
  }

  return (
    <div className="card" style={{ maxWidth: 420, margin: '60px auto' }}>
      <h2>🛡️ ZoneGuard AI — Login</h2>
      <p style={{ color: '#94a3b8' }}>Restricted Zone Contraband Detection</p>
      <form onSubmit={submit}>
        <label>Username</label>
        <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        <label>Password</label>
        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        {error && <p style={{ color: '#f87171' }}>{error}</p>}
        <button className="btn" style={{ marginTop: 16, width: '100%' }} type="submit">Login</button>
      </form>
      <p style={{ color: '#64748b', fontSize: 13, marginTop: 12 }}>
        Demo admin: <code>admin / admin123</code> (change after first login)
      </p>
    </div>
  )
}
