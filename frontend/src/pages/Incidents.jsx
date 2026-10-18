import React, { useEffect, useState } from 'react'
import client from '../api/client.js'

export default function Incidents() {
  const [rows, setRows] = useState([])
  const [zones, setZones] = useState([])
  const [f, setF] = useState({ date_from: '', date_to: '', zone_id: '', violation_type: '' })

  useEffect(() => { client.get('/zones').then((r) => setZones(r.data)); search() }, [])

  const search = async () => {
    const params = {}
    if (f.date_from) params.date_from = f.date_from
    if (f.date_to) params.date_to = f.date_to
    if (f.zone_id) params.zone_id = f.zone_id
    if (f.violation_type) params.violation_type = f.violation_type
    const r = await client.get('/incidents', { params })
    setRows(r.data)
  }

  const set = (k) => (e) => setF({ ...f, [k]: e.target.value })

  return (
    <>
      <h2>📋 Incident Log — Search & Filter (FR10)</h2>
      <div className="card">
        <div className="grid2">
          <div><label>From date</label><input type="date" value={f.date_from} onChange={set('date_from')} /></div>
          <div><label>To date</label><input type="date" value={f.date_to} onChange={set('date_to')} /></div>
          <div><label>Zone</label>
            <select value={f.zone_id} onChange={set('zone_id')}>
              <option value="">All zones</option>
              {zones.map((z) => <option key={z.id} value={z.id}>{z.name}</option>)}
            </select></div>
          <div><label>Violation type</label>
            <select value={f.violation_type} onChange={set('violation_type')}>
              <option value="">All types</option>
              <option value="smoking">smoking</option>
              <option value="mobile_phone">mobile_phone</option>
            </select></div>
        </div>
        <button className="btn" style={{ marginTop: 12 }} onClick={search}>🔍 Search</button>
      </div>
      <div className="card">
        <h3>Results ({rows.length})</h3>
        <table>
          <thead><tr><th>ID</th><th>Timestamp</th><th>Type</th><th>Zone</th><th>Conf.</th><th>Evidence</th></tr></thead>
          <tbody>
            {rows.map((i) => (
              <tr key={i.id}>
                <td>{i.id}</td>
                <td>{new Date(i.timestamp).toLocaleString()}</td>
                <td><span className={`badge badge-${i.violation_type}`}>{i.violation_type}</span></td>
                <td>{i.zone_name}</td>
                <td>{(i.confidence * 100).toFixed(1)}%</td>
                <td>{i.evidence_path &&
                  <a href={`/api/evidence/${i.evidence_path.split('/').pop()}`} target="_blank" rel="noreferrer">view</a>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
