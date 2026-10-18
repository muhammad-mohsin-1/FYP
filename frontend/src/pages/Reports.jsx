import React, { useState } from 'react'
import toast from 'react-hot-toast'
import client from '../api/client.js'

export default function Reports() {
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const download = async () => {
    try {
      const params = {}
      if (dateFrom) params.date_from = dateFrom
      if (dateTo) params.date_to = dateTo
      const r = await client.get('/reports/pdf', { params, responseType: 'blob' })
      const url = window.URL.createObjectURL(new Blob([r.data], { type: 'application/pdf' }))
      const a = document.createElement('a')
      a.href = url
      a.download = `compliance_report_${dateFrom || 'all'}_${dateTo || 'all'}.pdf`
      a.click()
      window.URL.revokeObjectURL(url)
      toast.success('PDF report downloaded')
    } catch {
      toast.error('Report generation failed')
    }
  }

  return (
    <>
      <h2>📄 Compliance Reports (FR11)</h2>
      <div className="card" style={{ maxWidth: 560 }}>
        <p style={{ color: '#94a3b8' }}>
          One-click formal summary of historical violations, generated from the
          database and downloaded as a standard PDF file.
        </p>
        <label>From date (optional)</label>
        <input type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
        <label>To date (optional)</label>
        <input type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
        <button className="btn" style={{ marginTop: 16 }} onClick={download}>
          ⬇ Download PDF report
        </button>
      </div>
    </>
  )
}
