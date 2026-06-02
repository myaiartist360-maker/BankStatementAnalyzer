import { useEffect, useState } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import BalanceChart from '../components/BalanceChart'
import TransactionTable from '../components/TransactionTable'
import RiskFlags from '../components/RiskFlags'
import TamperReport from '../components/TamperReport'
import MonthlyBreakdown from '../components/MonthlyBreakdown'
import CreditAssessment from '../components/CreditAssessment'
import FeedbackPanel from '../components/FeedbackPanel'

const API = '/api/v1'

const fmt = (n, decimals = 2) =>
  n == null ? '—' : `₹${Number(n).toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`

const STATUS_COLOR = {
  SUCCESS: 'var(--green)', PARTIAL: 'var(--amber)',
  TAMPER_DETECTED: 'var(--red)', PDF_DECRYPT_FAILED: 'var(--red)', EXTRACTION_FAILED: 'var(--red)',
}

export default function ResultsPage() {
  const { requestId } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [data, setData] = useState(location.state?.result || null)
  const [loading, setLoading] = useState(!data)
  const [tab, setTab] = useState('overview')

  useEffect(() => {
    if (!data && requestId) {
      fetch(`${API}/result/${requestId}`)
        .then(r => r.json()).then(setData).catch(() => setLoading(false))
        .finally(() => setLoading(false))
    }
  }, [requestId])

  if (loading) return (
    <div className="main-content" style={{ textAlign: 'center', paddingTop: 80 }}>
      <svg className="progress-ring" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--brand)" strokeWidth="2">
        <circle cx="12" cy="12" r="10" strokeOpacity="0.3"/>
        <path d="M12 2a10 10 0 0 1 10 10"/>
      </svg>
      <p style={{ marginTop: 16, color: 'var(--text-secondary)' }}>Loading results…</p>
    </div>
  )

  if (!data) return (
    <div className="main-content">
      <div className="card">
        <p>No result found for ID <code>{requestId}</code></p>
        <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => navigate('/')}>← New Analysis</button>
      </div>
    </div>
  )

  const s = data.summary || {}
  const sm = data.statement_metadata || {}
  const notes = data.processing_notes || []
  const isFailure = data.status && data.status !== 'SUCCESS'

  // Lightweight severity tagging for the on-screen log
  const noteLevel = (n) => {
    const t = n.toLowerCase()
    if (t.includes('error') || t.includes('failed') || t.includes('could not') || t.includes('no transactions')) return 'error'
    if (t.includes('warning') || t.includes('skipped') || t.includes('decrypt') || t.includes('tamper') || t.includes('mismatch') || t.includes('reordered')) return 'warn'
    return 'info'
  }
  const LEVEL_COLOR = { error: 'var(--red)', warn: 'var(--amber)', info: 'var(--text-muted)' }

  const ProcessingLog = ({ open }) => (
    <details className="card" open={open} style={{ marginBottom: 20, borderColor: isFailure ? 'var(--red)' : 'var(--glass-border)' }}>
      <summary style={{ cursor: 'pointer', listStyle: 'none', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600 }}>
        <span>🪵</span> Processing Log ({notes.length})
        <span style={{ marginLeft: 'auto', fontSize: 11, color: 'var(--text-muted)', fontWeight: 400 }}>extraction & integrity diagnostics</span>
      </summary>
      {notes.length === 0 ? (
        <p style={{ color: 'var(--text-muted)', fontSize: 13, marginTop: 12 }}>No diagnostics emitted.</p>
      ) : (
        <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 4, fontFamily: 'JetBrains Mono, monospace', fontSize: 11.5, maxHeight: 320, overflowY: 'auto' }}>
          {notes.map((n, i) => {
            const lvl = noteLevel(n)
            return (
              <div key={i} style={{ display: 'flex', gap: 8, padding: '3px 6px', background: i % 2 ? 'rgba(255,255,255,0.02)' : 'transparent', borderRadius: 4 }}>
                <span style={{ color: 'var(--text-muted)', minWidth: 24, textAlign: 'right' }}>{i + 1}</span>
                <span style={{ color: LEVEL_COLOR[lvl], minWidth: 48, textTransform: 'uppercase', fontSize: 10 }}>{lvl}</span>
                <span style={{ color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{n}</span>
              </div>
            )
          })}
        </div>
      )}
    </details>
  )

  return (
    <div className="main-content">
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 28 }}>
        <div>
          <h1 className="page-title">{sm.account_holder_name || 'Statement Analysis'}</h1>
          <p className="page-sub">
            {sm.bank_name && <span>{sm.bank_name} · </span>}
            {sm.account_number && <span className="mono">{sm.account_number} · </span>}
            {data.analysis_period?.from && <span>{data.analysis_period.from} → {data.analysis_period.to}</span>}
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span className="badge" style={{ background: STATUS_COLOR[data.status] + '22', color: STATUS_COLOR[data.status], fontSize: 12, padding: '6px 14px' }}>
            ● {data.status}
          </span>
          <button className="btn btn-secondary btn-sm" onClick={() => navigate('/')}>← New</button>
        </div>
      </div>

      {/* Failure banner + diagnostics (shown prominently when not fully successful) */}
      {isFailure && (
        <>
          <div className="card" style={{ marginBottom: 16, borderColor: 'var(--red)', background: 'var(--red-dim)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontSize: 28 }}>{data.status === 'PARTIAL' ? '⚠️' : '🚫'}</span>
              <div>
                <div style={{ fontWeight: 700, color: data.status === 'PARTIAL' ? 'var(--amber)' : 'var(--red)' }}>
                  {data.status === 'EXTRACTION_FAILED' && 'Could not extract transactions'}
                  {data.status === 'PDF_DECRYPT_FAILED' && 'Could not decrypt the PDF'}
                  {data.status === 'TAMPER_DETECTED' && 'Integrity checks failed'}
                  {data.status === 'PARTIAL' && 'Partial result'}
                </div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                  See the processing log below for the step-by-step diagnosis.
                </div>
              </div>
            </div>
          </div>
          <ProcessingLog open={true} />
        </>
      )}

      {/* Confidence bar */}
      <div className="card" style={{ marginBottom: 20, padding: '14px 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
          <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Extraction Confidence</span>
          <span style={{ fontSize: 13, fontWeight: 700 }}>{Math.round((data.confidence_score || 0) * 100)}%</span>
        </div>
        <div className="confidence-bar">
          <div className="confidence-fill" style={{ width: `${(data.confidence_score || 0) * 100}%` }} />
        </div>
      </div>

      {/* Stats grid */}
      <div className="stats-grid">
        {[
          { label: 'Total Transactions', value: s.total_transactions, sub: `${s.total_credit_transactions} credits / ${s.total_debit_transactions} debits`, accent: 'var(--brand-dim)' },
          { label: 'Total Credits',  value: fmt(s.total_credit_amount), sub: `Avg ${fmt(s.average_monthly_credit)}/mo`, accent: 'var(--green-dim)' },
          { label: 'Total Debits',   value: fmt(s.total_debit_amount),  sub: `Avg ${fmt(s.average_monthly_debit)}/mo`,  accent: 'var(--red-dim)' },
          { label: 'Avg EOD Balance', value: fmt(s.average_eod_balance), sub: s.minimum_eod_balance ? `Min ${fmt(s.minimum_eod_balance?.amount)}` : '', accent: 'var(--amber-dim)' },
          { label: 'Salary',  value: s.salary_identified ? fmt(s.probable_salary_amount) : 'Not detected', sub: s.salary_identified ? 'Identified' : '', accent: 'var(--green-dim)' },
          { label: 'EMI Bounces',  value: s.emi_bounces, sub: `Cheque bounces: ${s.inward_cheque_bounces}`, accent: s.emi_bounces > 0 ? 'var(--red-dim)' : 'var(--green-dim)' },
          { label: 'Gambling',  value: s.gambling_transaction_count, sub: s.gambling_transaction_count ? fmt(s.gambling_total_amount) : 'Clean', accent: s.gambling_transaction_count ? 'var(--purple-dim)' : 'var(--green-dim)' },
          { label: 'High-Risk Flags', value: (data.high_risk_flags || []).length, sub: 'See Risk tab', accent: (data.high_risk_flags || []).length ? 'var(--red-dim)' : 'var(--green-dim)' },
          { label: 'Credit Score', value: data.credit_assessment ? `${data.credit_assessment.credit_score} · ${data.credit_assessment.risk_band}` : '—', sub: data.credit_assessment ? `FOIR ${data.credit_assessment.foir != null ? Math.round(data.credit_assessment.foir * 100) + '%' : '—'}` : 'See Credit tab', accent: 'var(--cyan-dim, var(--brand-dim))' },
        ].map(stat => (
          <div key={stat.label} className="stat-card" style={{ '--accent-color': stat.accent }}>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-value">{stat.value ?? '—'}</div>
            {stat.sub && <div className="stat-sub">{stat.sub}</div>}
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="tabs">
        {[['overview','📊 Overview'],['credit','📈 Credit'],['transactions','📋 Transactions'],['risk','🚨 Risk'],['tamper','🔍 Tamper'],['feedback','💬 Feedback']].map(([id,label]) => (
          <button key={id} className={`tab ${tab === id ? 'active' : ''}`} onClick={() => setTab(id)}>{label}</button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'overview' && (
        <div style={{ display: 'grid', gap: 20 }}>
          <BalanceChart transactions={data.raw_transactions || []} />
          <MonthlyBreakdown credits={data.monthly_credits || []} debits={data.monthly_debits || []} />

          {/* Obligations */}
          <div className="card">
            <div className="section-title"><span>📌</span> Obligation Indicators</div>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {[
                ['Loan Repayments', data.obligation_indicators?.loan_repayments_detected],
                ['Insurance Premiums', data.obligation_indicators?.insurance_premiums_detected],
              ].map(([label, val]) => (
                <span key={label} className={`badge ${val ? 'badge-warning' : 'badge-success'}`}>
                  {val ? '⚠️' : '✓'} {label}
                </span>
              ))}
              {data.obligation_indicators?.recurring_utility_payments > 0 && (
                <span className="badge badge-info">💡 {data.obligation_indicators.recurring_utility_payments} Utility Payment(s)</span>
              )}
            </div>
          </div>

          {/* EMI */}
          {data.emi_analysis?.count > 0 && (
            <div className="card">
              <div className="section-title"><span>💳</span> EMI Detected</div>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 12 }}>
                Probable EMI: <strong style={{ color: 'var(--text-primary)' }}>{fmt(data.emi_analysis.probable_emi_amount)}/mo</strong>
                {data.emi_analysis.lender_hint && <> · Lender hint: <code style={{ color: 'var(--brand)' }}>{data.emi_analysis.lender_hint}</code></>}
              </p>
            </div>
          )}

          {/* Processing log (collapsed on success — already shown above on failure) */}
          {!isFailure && notes.length > 0 && <ProcessingLog open={false} />}
        </div>
      )}

      {tab === 'credit' && <CreditAssessment assessment={data.credit_assessment} />}
      {tab === 'transactions' && <TransactionTable transactions={data.raw_transactions || []} />}
      {tab === 'risk' && <RiskFlags flags={data.high_risk_flags || []} gambling={data.gambling_analysis} crypto={data.crypto_analysis} roundTrip={data.round_trip_analysis} hvcash={data.high_value_cash_analysis} />}
      {tab === 'tamper' && <TamperReport report={data.tamper_report} />}
      {tab === 'feedback' && <FeedbackPanel requestId={data.request_id} />}
    </div>
  )
}
