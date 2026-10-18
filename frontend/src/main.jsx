import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
      {/* Red toast alerts for violations (FR6) */}
      <Toaster position="top-right" toastOptions={{
        style: { background: '#dc2626', color: '#fff', fontWeight: 600 },
        duration: 6000,
      }} />
    </BrowserRouter>
  </React.StrictMode>
)
