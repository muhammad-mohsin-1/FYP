import React, { useEffect, useState, useRef } from 'react'
import toast from 'react-hot-toast'
import client from '../api/client.js'

export default function Dashboard() {
  const [zones, setZones] = useState([])
  const [zoneId, setZoneId] = useState('')
  const [file, setFile] = useState(null)
  const [threshold, setThreshold] = useState(0.45)
  const [running, setRunning] = useState(false)
  const [result, setResult] = useState(null)
  const [recent, setRecent] = useState([])
  const wsRef = useRef(null)

  useEffect(() => {
    client.get('/zones').then((r) => {
      setZones(r.data)
      if (r.data.length) setZoneId(r.data[0].id)
    })
    client.get('/settings/threshold').then((r) => setThreshold(r.data.threshold))
    refreshRecent()
    // FR6: live red-toast alerts over WebSocket
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(`${proto}://${window.location.host}/ws/alerts`)
    ws.onmessage = (ev) => {
      const a = JSON.parse(ev.data)
      if (a.type === 'violation') {
        toast(`🚨 ${a.violation_type.toUpperCase()} detected in ${a.zone} (${(a.confidence * 100).toFixed(0)}%)`,
          { style: { background: '#dc2626', color: '#fff', fontWeight: 700 } })
        refreshRecent()
      }
    }
    wsRef.current = ws
    return () => ws.close()
  }, [])

  const refreshRecent = () =>
    client.get('/incidents').then((r) => setRecent(r.data.slice(0, 8)))

  const onThreshold = async (v) => {
    setThreshold(v)
    await client.post('/settings/threshold', { threshold: v })
  }

  const run = async () => {
    if (!file || !zoneId) return toast.error('Select a video and a camera zone first')
    setRunning(true); setResult(null)
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('camera_location', zones.find((z) => z.id === Number(zoneId))?.name || '')
      const up = await client.post('/videos/upload', form)
      const det = await client.post('/detect/run', {
        video_id: up.data.video_id, zone_id: Number(zoneId), frame_skip: 5,
      })
      setResult(det.data)
      toast.success(`Scan complete: ${det.data.incidents_created} incident(s) found`)
      refreshRecent()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Detection failed')
    } finally {
      setRunning(false)
    }
  }

  return (
    <>
      <h2>📹 Live Monitor</h2>
      <div className="grid2">
        <div className="card">
          <h3>Video Source (FR4)</h3>
          <label>Camera location / restricted zone</label>
          <select value={zoneId} onChange={(e) => setZoneId(e.target.value)}>
            {zones.map((z) => <option key={z.id} value={z.id}>{z.name}</option>)}
          </select>
          <label>Upload video file</label>
          <input type="file" accept="video/*" onChange={(e) => setFile(e.target.files[0])} />
          <label>Confidence threshold: {(threshold * 100).toFixed(0)}% (FR3)</label>
          <input type="range" min="0.05" max="0.95" step="0.05" value={threshold}
            onChange={(e) => onThreshold(Number(e.target.value))} />
          <button className="btn" style={{ marginTop: 16 }} onClick={run} disabled={running}>
            {running ? '⏳ Scanning…' : '▶ Run YOLOv11 Detection (FR5)'}
          </button>
          {result && (
            <p style={{ marginTop: 12 }}>
              Frames: {result.frames_processed} | Incidents: <strong>{result.incidents_created}</strong> |
              Time: {result.elapsed_seconds}s
            </p>
          )}
        </div>
        <div className="card">
          <h3>Latest Incidents</h3>
          <table>
            <thead><tr><th>Time</th><th>Type</th><th>Zone</th><th>Conf.</th><th>Evidence</th></tr></thead>
            <tbody>
              {recent.map((i) => (
                <tr key={i.id}>
                  <td>{new Date(i.timestamp).toLocaleString()}</td>
                  <td><span className={`badge badge-${i.violation_type}`}>{i.violation_type}</span></td>
                  <td>{i.zone_name}</td>
                  <td>{(i.confidence * 100).toFixed(0)}%</td>
                  <td>{i.evidence_path &&
                    <a href={`/api/evidence/${i.evidence_path.split('/').pop()}`} target="_blank" rel="noreferrer">
                      <img className="evidence-thumb" src={`/api/evidence/${i.evidence_path.split('/').pop()}`} alt="evidence" />
                    </a>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </>
  )
}
