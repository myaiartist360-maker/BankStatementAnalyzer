import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'

const API = '/api/v1'

const BANKS = ['HDFC Bank', 'SBI', 'ICICI Bank', 'Axis Bank', 'Kotak Mahindra', 'Yes Bank', 'Other']

function toBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result.split(',')[1])
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

export default function UploadPage() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [inputType, setInputType] = useState('pdf')
  const [aaJson, setAaJson] = useState('')
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [hint, setHint] = useState({ dob: '', account_number_last4: '', pan_last4: '', mobile_last4: '', custom_password: '' })
  const [period, setPeriod] = useState({ from: '', to: '' })
  const [meta, setMeta] = useState({ account_holder_name: '', account_number: '', bank_name: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [errorDetails, setErrorDetails] = useState('')

  const onDrop = useCallback(accepted => {
    if (accepted[0]) {
      setFile(accepted[0])
      if (accepted[0].name.endsWith('.zip')) setInputType('zip')
      else setInputType('pdf')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/zip': ['.zip'] },
    multiple: false,
    disabled: inputType === 'account_aggregator_json',
  })

  const handleSubmit = async () => {
    setError('')
    setLoading(true)

    try {
      let body = { input_type: inputType }

      if (inputType === 'account_aggregator_json') {
        try { body.aa_json = JSON.parse(aaJson) }
        catch { setError('Invalid JSON in AA payload'); setLoading(false); return }
      } else {
        if (!file) { setError('Please select a file'); setLoading(false); return }
        body.file = await toBase64(file)
      }

      // Optional hints
      const hintClean = Object.fromEntries(Object.entries(hint).filter(([,v]) => v.trim()))
      if (Object.keys(hintClean).length) body.password_hint = hintClean

      if (period.from && period.to) body.analysis_period = { from: period.from, to: period.to }

      const metaClean = Object.fromEntries(Object.entries(meta).filter(([,v]) => v.trim()))
      if (Object.keys(metaClean).length) body.metadata = metaClean

      const res = await fetch(`${API}/analyse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      
      if (!res.ok) {
        let errStr = `HTTP ${res.status}`
        try {
          const textBody = await res.text()
          try {
            const errData = JSON.parse(textBody)
            errStr = errData.detail?.[0]?.msg || errData.detail || errData.processing_notes?.[0] || JSON.stringify(errData)
          } catch {
            errStr = textBody || res.statusText
          }
        } catch {
          errStr = res.statusText
        }
        throw new Error(errStr)
      }
      
      const data = await res.json()
      navigate(`/results/${data.request_id}`, { state: { result: data } })
    } catch (e) {
      console.error(e)
      let debugInfo = e.stack || e.toString()
      if (e.message === 'Failed to fetch') {
        debugInfo += '\n\n💡 DIAGNOSIS:\nThe browser network request failed completely. This usually means:\n1. The backend FastAPI server is NOT running on port 8000.\n2. The Vite proxy failed to reach the backend.\nPlease open your terminal and ensure `python main.py` is actively running without any crash logs.'
      }
      setError(`Request failed: ${e.message}`)
      setErrorDetails(debugInfo)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="main-content" style={{ maxWidth: 760 }}>
      <h1 className="page-title">Bank Statement Analyser</h1>
      <p className="page-sub">Upload a PDF, ZIP, or paste an Account Aggregator JSON to get a full financial analysis report.</p>

      {/* Input type selector */}
      <div className="card" style={{ marginBottom: 20 }}>
        <div className="section-title"><span>📥</span> Input Type</div>
        <div style={{ display: 'flex', gap: 10 }}>
          {[['pdf','PDF Statement'],['zip','ZIP Archive'],['account_aggregator_json','AA JSON']].map(([val,label]) => (
            <button key={val}
              className={`btn ${inputType === val ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setInputType(val)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* File upload / AA JSON */}
      {inputType === 'account_aggregator_json' ? (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-title"><span>📋</span> Account Aggregator JSON</div>
          <textarea
            className="form-input"
            rows={8}
            placeholder='{"fipId": "...", "Transactions": {...}}'
            value={aaJson}
            onChange={e => setAaJson(e.target.value)}
            style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, resize: 'vertical' }}
          />
        </div>
      ) : (
        <div className="card" style={{ marginBottom: 20 }}>
          <div className="section-title"><span>📄</span> Upload File</div>
          <div {...getRootProps()} className={`upload-zone ${isDragActive ? 'active' : ''}`}>
            <input {...getInputProps()} />
            <div className="upload-icon">{file ? '✅' : '☁️'}</div>
            {file ? (
              <>
                <div className="upload-title">{file.name}</div>
                <div className="upload-sub">{(file.size / 1024).toFixed(1)} KB — click to change</div>
              </>
            ) : (
              <>
                <div className="upload-title">Drop your statement here</div>
                <div className="upload-sub">PDF or ZIP · Click or drag &amp; drop</div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Advanced options */}
      <div className="card" style={{ marginBottom: 20 }}>
        <button
          onClick={() => setShowAdvanced(p => !p)}
          style={{ background: 'none', border: 'none', color: 'var(--brand)', fontSize: 14, fontWeight: 600, padding: 0, display: 'flex', alignItems: 'center', gap: 6 }}>
          {showAdvanced ? '▾' : '▸'} Advanced Options (Password Hints / Period / Metadata)
        </button>

        {showAdvanced && (
          <div style={{ marginTop: 20, display: 'grid', gap: 24 }}>
            {/* Password hints */}
            <div>
              <div className="section-title" style={{ fontSize: 13 }}><span>🔐</span> Password Hints</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                {[['dob','Date of Birth (DDMMYYYY)'],['account_number_last4','Account Last 4'],['pan_last4','PAN Last 4'],['mobile_last4','Mobile Last 4'],['custom_password','Exact Password']].map(([k,label]) => (
                  <div className="form-group" key={k}>
                    <label className="form-label">{label}</label>
                    <input className="form-input" value={hint[k]} onChange={e => setHint(h => ({...h,[k]:e.target.value}))} placeholder={k === 'dob' ? '15081990' : ''} />
                  </div>
                ))}
              </div>
            </div>

            {/* Analysis period */}
            <div>
              <div className="section-title" style={{ fontSize: 13 }}><span>📅</span> Analysis Period (optional)</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">From</label>
                  <input type="date" className="form-input" value={period.from} onChange={e => setPeriod(p => ({...p,from:e.target.value}))} />
                </div>
                <div className="form-group">
                  <label className="form-label">To</label>
                  <input type="date" className="form-input" value={period.to} onChange={e => setPeriod(p => ({...p,to:e.target.value}))} />
                </div>
              </div>
            </div>

            {/* Cross-validation metadata */}
            <div>
              <div className="section-title" style={{ fontSize: 13 }}><span>✅</span> Cross-Validation (optional)</div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div className="form-group">
                  <label className="form-label">Account Holder Name</label>
                  <input className="form-input" value={meta.account_holder_name} onChange={e => setMeta(m => ({...m,account_holder_name:e.target.value}))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Account Number</label>
                  <input className="form-input" value={meta.account_number} onChange={e => setMeta(m => ({...m,account_number:e.target.value}))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Bank Name</label>
                  <select className="form-input" value={meta.bank_name} onChange={e => setMeta(m => ({...m,bank_name:e.target.value}))}>
                    <option value="">— select —</option>
                    {BANKS.map(b => <option key={b}>{b}</option>)}
                  </select>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div style={{ background: 'var(--red-dim)', border: '1px solid var(--red)', borderRadius: 10, padding: '12px 16px', marginBottom: 16, color: 'var(--red)', fontSize: 13 }}>
          <div style={{ fontWeight: 600, marginBottom: errorDetails ? 12 : 0 }}>⚠️ {error}</div>
          {errorDetails && (
            <pre style={{ margin: 0, padding: 12, background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: 6, fontSize: 11, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', maxHeight: 200, overflowY: 'auto' }}>
              {errorDetails}
            </pre>
          )}
        </div>
      )}

      <button className="btn btn-primary btn-lg" onClick={handleSubmit} disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
        {loading ? (
          <><svg className="progress-ring" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" strokeOpacity="0.3"/><path d="M12 2a10 10 0 0 1 10 10"/></svg> Analysing…</>
        ) : '🔍 Analyse Statement'}
      </button>
    </div>
  )
}
