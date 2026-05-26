import { useEffect, useState } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import BalanceChart from '../components/BalanceChart'
import TransactionTable from '../components/TransactionTable'
import RiskFlags from '../components/RiskFlags'
import TamperReport from '../components/TamperReport'
import MonthlyBreakdown from '../components/MonthlyBreakdown'

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
        {[['overview','📊 Overview'],['transactions','📋 Transactions'],['risk','🚨 Risk'],['tamper','🔍 Tamper']].map(([id,label]) => (
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

          {/* Processing notes */}
          {data.processing_notes?.length > 0 && (
            <div className="card">
              <div className="section-title"><span>📝</span> Processing Notes</div>
              <ul style={{ listStyle: 'none', paddingLeft: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {data.processing_notes.map((n, i) => (
                  <li key={i} style={{ fontSize: 12, color: 'var(--text-secondary)', display: 'flex', gap: 8 }}>
                    <span style={{ color: 'var(--brand)' }}>›</span> {n}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {tab === 'transactions' && <TransactionTable transactions={data.raw_transactions || []} />}
      {tab === 'risk' && <RiskFlags flags={data.high_risk_flags || []} gambling={data.gambling_analysis} crypto={data.crypto_analysis} roundTrip={data.round_trip_analysis} hvcash={data.high_value_cash_analysis} />}
      {tab === 'tamper' && <TamperReport report={data.tamper_report} />}
    </div>
  )
}
