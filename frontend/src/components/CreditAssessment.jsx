import { useMemo } from 'react'

const fmt = n => n == null ? '—' : `₹${Number(n).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`
const pct = n => n == null ? '—' : `${(n * 100).toFixed(0)}%`

const BAND_COLOR = {
  EXCELLENT: 'var(--green)',
  GOOD: 'var(--cyan)',
  FAIR: 'var(--amber)',
  WEAK: 'var(--amber)',
  POOR: 'var(--red)',
}

const SUB_LABELS = {
  income_stability: 'Income Stability',
  savings_capacity: 'Savings Capacity',
  balance_health: 'Balance Health',
  obligation_burden: 'Obligation Burden',
  conduct: 'Account Conduct',
}

function ScoreGauge({ score, band }) {
  const color = BAND_COLOR[band] || 'var(--text-muted)'
  const r = 54
  const circ = 2 * Math.PI * r
  const offset = circ * (1 - score / 100)
  return (
    <div style={{ position: 'relative', width: 140, height: 140, flexShrink: 0 }}>
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r={r} fill="none" stroke="var(--glass-border)" strokeWidth="12" />
        <circle
          cx="70" cy="70" r={r} fill="none" stroke={color} strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={circ} strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ fontSize: 34, fontWeight: 800, color, lineHeight: 1 }}>{score}</div>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>/ 100</div>
      </div>
    </div>
  )
}

function Ratio({ label, value, hint, danger }) {
  return (
    <div className="stat-card" style={{ '--accent-color': danger ? 'var(--red-dim)' : 'var(--brand-dim)' }}>
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={{ fontSize: 22, color: danger ? 'var(--red)' : 'var(--text-primary)' }}>{value}</div>
      {hint && <div className="stat-sub">{hint}</div>}
    </div>
  )
}

export default function CreditAssessment({ assessment }) {
  if (!assessment) return (
    <div className="card">
      <div className="section-title"><span>📈</span> Credit Assessment</div>
      <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Credit assessment not available for this result.</p>
    </div>
  )

  const a = assessment
  const band = a.risk_band
  const color = BAND_COLOR[band] || 'var(--text-muted)'
  const foirDanger = a.foir != null && a.foir > 0.55
  const surplusDanger = a.net_monthly_surplus < 0

  const subScores = useMemo(
    () => Object.entries(a.sub_scores || {}).sort((x, y) => y[1] - x[1]),
    [a.sub_scores]
  )

  return (
    <div style={{ display: 'grid', gap: 20 }}>
      {/* Score header */}
      <div className="card" style={{ display: 'flex', gap: 24, alignItems: 'center', flexWrap: 'wrap', borderColor: color + '55' }}>
        <ScoreGauge score={a.credit_score ?? 0} band={band} />
        <div style={{ flex: 1, minWidth: 240 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span className="badge" style={{ background: color + '22', color, fontSize: 13, padding: '4px 12px' }}>{band}</span>
            <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Cash-flow credit score</span>
          </div>
          <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
            {a.recommendation}
          </div>
          <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: 0 }}>
            Advisory only — derived from statement cash-flows. Final lending decision rests with the underwriter.
          </p>
        </div>
      </div>

      {/* Key lending ratios */}
      <div className="stats-grid">
        <Ratio label="Est. Monthly Income" value={fmt(a.monthly_income_estimate)}
          hint={a.income_basis === 'detected_salary' ? 'From detected salary' : 'Avg monthly credit'} />
        <Ratio label="FOIR (Obligation / Income)" value={pct(a.foir)} danger={foirDanger}
          hint={`Obligations ${fmt(a.monthly_obligations_estimate)}/mo`} />
        <Ratio label="Net Monthly Surplus" value={fmt(a.net_monthly_surplus)} danger={surplusDanger}
          hint={`Savings rate ${pct(a.savings_rate)}`} />
        <Ratio label="Inflow / Outflow" value={a.inflow_outflow_ratio != null ? a.inflow_outflow_ratio.toFixed(2) : '—'}
          hint="Credits ÷ debits" />
        <Ratio label="Avg Bank Balance" value={fmt(a.average_bank_balance)}
          hint={a.negative_balance_days ? `${a.negative_balance_days} negative day(s)` : 'No negative days'}
          danger={a.negative_balance_days > 0} />
        <Ratio label="Income Volatility" value={a.income_volatility != null ? a.income_volatility.toFixed(2) : '—'}
          hint="CV — lower is steadier" danger={a.income_volatility != null && a.income_volatility > 0.45} />
      </div>

      {/* Sub-score breakdown */}
      <div className="card">
        <div className="section-title"><span>🧮</span> Score Components</div>
        <div style={{ display: 'grid', gap: 12 }}>
          {subScores.map(([key, val]) => {
            const w = (a.sub_score_weights?.[key] ?? 0) * 100
            const barColor = val >= 70 ? 'var(--green)' : val >= 50 ? 'var(--amber)' : 'var(--red)'
            return (
              <div key={key}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, marginBottom: 4 }}>
                  <span style={{ color: 'var(--text-secondary)' }}>{SUB_LABELS[key] || key} <span style={{ color: 'var(--text-muted)' }}>· {w.toFixed(0)}% weight</span></span>
                  <span style={{ fontWeight: 700 }}>{val}</span>
                </div>
                <div className="confidence-bar">
                  <div className="confidence-fill" style={{ width: `${val}%`, background: barColor }} />
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Factors */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 20 }}>
        <div className="card">
          <div className="section-title"><span>✅</span> Positive Factors</div>
          {(a.positive_factors || []).length === 0
            ? <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>None identified.</p>
            : <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {a.positive_factors.map((f, i) => (
                  <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 8 }}>
                    <span style={{ color: 'var(--green)' }}>+</span> {f}
                  </li>
                ))}
              </ul>}
        </div>
        <div className="card">
          <div className="section-title"><span>⚠️</span> Risk Factors</div>
          {(a.negative_factors || []).length === 0
            ? <p style={{ color: 'var(--green)', fontSize: 13 }}>No adverse factors detected.</p>
            : <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {a.negative_factors.map((f, i) => (
                  <li key={i} style={{ fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 8 }}>
                    <span style={{ color: 'var(--red)' }}>−</span> {f}
                  </li>
                ))}
              </ul>}
        </div>
      </div>
    </div>
  )
}
