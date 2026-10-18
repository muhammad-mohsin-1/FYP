import React, { useEffect, useState } from 'react'
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import client from '../api/client.js'

const COLORS = ['#dc2626', '#f59e0b', '#2563eb', '#16a34a', '#9333ea']

export default function Analytics() {
  const [data, setData] = useState(null)
  useEffect(() => { client.get('/analytics/summary').then((r) => setData(r.data)) }, [])
  if (!data) return <p>Loading…</p>

  const byType = Object.entries(data.by_type).map(([name, value]) => ({ name, value }))
  const byZone = Object.entries(data.by_zone).map(([name, value]) => ({ name, value }))
  const byDay = Object.entries(data.by_day).map(([name, value]) => ({ name, value }))

  return (
    <>
      <h2>📊 Analytics Dashboard (FR9)</h2>
      <div className="card"><h3>Total incidents: {data.total_incidents}</h3></div>
      <div className="grid2">
        <div className="card">
          <h3>Violations by type (pie)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie data={byType} dataKey="value" nameKey="name" label outerRadius={100}>
                {byType.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie>
              <Tooltip /><Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="card">
          <h3>Violations by zone (bar)</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={byZone}>
              <XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip />
              <Bar dataKey="value" fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
      <div className="card">
        <h3>Violations per day (bar)</h3>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={byDay}>
            <XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip />
            <Bar dataKey="value" fill="#16a34a" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </>
  )
}
