import { useState } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import './index.css'
import UploadPage from './pages/UploadPage'
import ResultsPage from './pages/ResultsPage'

function Topbar() {
  return (
    <header className="topbar">
      <div className="topbar-logo">
        <div className="topbar-logo-icon">📊</div>
        <span>BSA Engine</span>
      </div>
      <div style={{ flex: 1 }} />
      <span style={{ fontSize: 12, color: 'var(--text-muted)', fontFamily: 'JetBrains Mono, monospace' }}>
        v1.0.0 · Indian FI Statement Analyser
      </span>
    </header>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Topbar />
        <main>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/results/:requestId" element={<ResultsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
