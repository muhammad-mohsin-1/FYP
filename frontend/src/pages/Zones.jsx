import React, { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import client from '../api/client.js'

export default function Zones() {
  const [zones, setZones] = useState([])
  const [name, setName] = useState('')
  const [desc, setDesc] = useState('')
  const [editing, setEditing] = useState(null)

  const load = () => client.get('/zones').then((r) => setZones(r.data))
  useEffect(load, [])

  const save = async () => {
    if (!name.trim()) return toast.error('Zone name required')
    try {
      if (editing) {
        await client.put(`/zones/${editing}`, { name, description: desc })
        toast.success('Zone updated')
      } else {
        await client.post('/zones', { name, description: desc })
        toast.success('Zone added')
      }
      setName(''); setDesc(''); setEditing(null); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  const remove = async (id, n) => {
    if (!window.confirm(`Remove zone "${n}"?`)) return
    await client.delete(`/zones/${id}`)
    toast.success('Zone removed'); load()
  }

  return (
    <>
      <h2>📍 Zone Configuration (Admin)</h2>
      <div className="card">
        <h3>{editing ? 'Update zone' : 'Add restricted zone'}</h3>
        <label>Zone name</label>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Server Room" />
        <label>Description</label>
        <input value={desc} onChange={(e) => setDesc(e.target.value)} placeholder="Why is it restricted?" />
        <button className="btn" style={{ marginTop: 12 }} onClick={save}>
          {editing ? 'Update' : 'Add'} zone
        </button>
        {editing && <button className="btn" style={{ marginLeft: 8 }} onClick={() => { setEditing(null); setName(''); setDesc('') }}>Cancel</button>}
      </div>
      <div className="card">
        <h3>Existing zones</h3>
        <table>
          <thead><tr><th>ID</th><th>Name</th><th>Description</th><th>Actions</th></tr></thead>
          <tbody>
            {zones.map((z) => (
              <tr key={z.id}>
                <td>{z.id}</td><td>{z.name}</td><td>{z.description}</td>
                <td>
                  <button className="btn" onClick={() => { setEditing(z.id); setName(z.name); setDesc(z.description) }}>Edit</button>{' '}
                  <button className="btn btn-danger" onClick={() => remove(z.id, z.name)}>Remove</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
