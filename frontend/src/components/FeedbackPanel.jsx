import { useState } from 'react'

const API = '/api/v1'

const SECTIONS = [
  ['salary_correct', 'Salary detection'],
  ['emi_correct', 'EMI detection'],
  ['tamper_correct', 'Tamper verdict'],
  ['risk_flags_correct', 'Risk flags'],
  ['transactions_parsed_correctly', 'Transaction parsing'],
  ['credit_assessment_useful', 'Credit assessment'],
]

function Stars({ value, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 6 }}>
      {[1, 2, 3, 4, 5].map(n => (
        <button
          key={n}
          type="button"
          onClick={() => onChange(n)}
          style={{
            background: 'none', border: 'none', cursor: 'pointer', padding: 0,
            fontSize: 28, lineHeight: 1, color: n <= value ? 'var(--amber)' : 'var(--glass-border)',
            transition: 'color .15s',
          }}
          aria-label={`${n} star`}
        >★</button>
      ))}
    </div>
  )
}

function Tri({ label, value, onChange }) {
  // value: true | false | null
  const opt = (val, txt, color) => (
    <button
      type="button"
      onClick={() => onChange(value === val ? null : val)}
      className={`btn btn-sm ${value === val ? 'btn-primary' : 'btn-secondary'}`}
      style={value === val ? { background: color, borderColor: color } : {}}
    >{txt}</button>
  )
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '8px 0', borderBottom: '1px solid var(--glass-border)' }}>
      <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{label}</span>
      <div style={{ display: 'flex', gap: 6 }}>
        {opt(true, '👍 Correct', 'var(--green)')}
        {opt(false, '👎 Wrong', 'var(--red)')}
      </div>
    </div>
  )
}

export default function FeedbackPanel({ requestId }) {
  const [rating, setRating] = useState(0)
  const [sections, setSections] = useState({})
  const [correctedSalary, setCorrectedSalary] = useState('')
  const [falsePositives, setFalsePositives] = useState('')
  const [missed, setMissed] = useState('')
  const [comments, setComments] = useState('')
  const [reviewer, setReviewer] = useState('')
  const [status, setStatus] = useState('idle') // idle | sending | done | error
  const [error, setError] = useState('')

  const setSection = (k, v) => setSections(s => ({ ...s, [k]: v }))

  const submit = async () => {
    setStatus('sending'); setError('')
    const body = {
      request_id: requestId,
      overall_rating: rating || null,
      sections,
      corrected_salary_amount: correctedSalary ? Number(correctedSalary) : null,
      false_positive_flags: falsePositives.split(',').map(s => s.trim()).filter(Boolean),
      missed_flags: missed.split(',').map(s => s.trim()).filter(Boolean),
      comments: comments.trim() || null,
      reviewer: reviewer.trim() || null,
    }
    try {
      const res = await fetch(`${API}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) {
        const t = await res.text()
        throw new Error(t || `HTTP ${res.status}`)
      }
      setStatus('done')
    } catch (e) {
      setError(e.message)
      setStatus('error')
    }
  }

  if (status === 'done') return (
    <div className="card" style={{ textAlign: 'center', padding: '40px 24px' }}>
      <div style={{ fontSize: 44, marginBottom: 12 }}>🙏</div>
      <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--green)' }}>Thank you for your feedback!</div>
      <p style={{ color: 'var(--text-secondary)', fontSize: 13, marginTop: 8 }}>
        Your review is stored and helps tune the analysis engine's detection accuracy.
      </p>
      <button className="btn btn-secondary btn-sm" style={{ marginTop: 16 }} onClick={() => { setStatus('idle'); setRating(0); setSections({}); setComments('') }}>
        Submit another review
      </button>
    </div>
  )

  return (
    <div style={{ display: 'grid', gap: 20 }}>
      <div className="card">
        <div className="section-title"><span>💬</span> Rate this analysis</div>
        <p style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: -6, marginBottom: 16 }}>
          Help improve the engine. Tell us where it was right or wrong — this feedback is logged as a quality signal for tuning thresholds and heuristics.
        </p>

        <label className="form-label">Overall accuracy</label>
        <Stars value={rating} onChange={setRating} />
      </div>

      <div className="card">
        <div className="section-title"><span>🎯</span> Section accuracy</div>
        {SECTIONS.map(([k, label]) => (
          <Tri key={k} label={label} value={sections[k] ?? null} onChange={v => setSection(k, v)} />
        ))}
      </div>

      <div className="card">
        <div className="section-title"><span>✏️</span> Corrections</div>
        <div style={{ display: 'grid', gap: 16 }}>
          <div className="form-group">
            <label className="form-label">Corrected monthly salary (₹) — if the engine got it wrong</label>
            <input className="form-input" type="number" value={correctedSalary}
              onChange={e => setCorrectedSalary(e.target.value)} placeholder="e.g. 85000" />
          </div>
          <div className="form-group">
            <label className="form-label">False-positive flags (comma-separated)</label>
            <input className="form-input" value={falsePositives}
              onChange={e => setFalsePositives(e.target.value)} placeholder="GAMBLING_TRANSACTIONS, ..." />
          </div>
          <div className="form-group">
            <label className="form-label">Missed risks the engine should have caught (comma-separated)</label>
            <input className="form-input" value={missed}
              onChange={e => setMissed(e.target.value)} placeholder="undisclosed loan, ..." />
          </div>
          <div className="form-group">
            <label className="form-label">Comments</label>
            <textarea className="form-input" rows={3} value={comments}
              onChange={e => setComments(e.target.value)} placeholder="Anything else worth noting…" style={{ resize: 'vertical' }} />
          </div>
          <div className="form-group">
            <label className="form-label">Your name / analyst id (optional)</label>
            <input className="form-input" value={reviewer} onChange={e => setReviewer(e.target.value)} />
          </div>
        </div>

        {status === 'error' && (
          <div style={{ background: 'var(--red-dim)', border: '1px solid var(--red)', borderRadius: 8, padding: '10px 14px', marginTop: 16, color: 'var(--red)', fontSize: 13 }}>
            ⚠️ Could not submit feedback: {error}
          </div>
        )}

        <button className="btn btn-primary btn-lg" style={{ width: '100%', justifyContent: 'center', marginTop: 20 }}
          disabled={status === 'sending' || (!rating && Object.keys(sections).length === 0)}
          onClick={submit}>
          {status === 'sending' ? 'Submitting…' : '📨 Submit Feedback'}
        </button>
      </div>
    </div>
  )
}
