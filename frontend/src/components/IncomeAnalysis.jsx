import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const fmt = (n, d = 0) => n == null ? '—' : `₹${Number(n).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d })}`
const fmtK = n => `₹${(n / 1000).toFixed(0)}k`

const CAT_ICON = {
  SALARY: '💼', BUSINESS: '🏪', INTEREST: '🏦', RENT: '🏠',
  FOREX_INWARD: '🌐', GOVT: '🏛️', MATURITY: '📈', TAX_REFUND: '🧾',
  REFUND_REV: '↩️', CAPITAL: '💰', AGRI: '🌾', PIGMY: '🪙',
  CASH_DEPOSIT: '💵', TRANSFER_IN: '🔁', OTHER: '➕',
}

const TXN_COLUMNS = [
  { key: 'date', label: 'Date', type: 'date' },
  { key: 'narration', label: 'Narration', type: 'text' },
  { key: 'mode', label: 'Mode', type: 'text' },
  { key: 'amount', label: 'Amount', type: 'credit', align: 'right' },
]

export default function IncomeAnalysis({ income, onDrill }) {
  if (!income || !income.sources?.length) return (
    <div className="card">
      <div className="section-title"><span>💰</span> Income Analysis</div>
      <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No credit transactions available to categorise.</p>
    </div>
  )

  const maxShare = Math.max(...income.sources.map(s => s.share_pct || 0), 1)
  const trend = (income.monthly_breakdown || []).map(m => ({ month: m.month?.slice(5), full: m.month, amount: m.amount }))

  const openSource = (s) => onDrill({
    title: `${s.label}`,
    subtitle: `${s.count} credit(s) · ${s.recurring ? 'Recurring' : 'One-off'} · ${s.share_pct}% of total income`,
    value: fmt(s.total_amount, 2),
    formula:
      `category = first keyword/mode match on narration\n` +
      `total = Σ credit_amount of ${s.count} matched txn(s) = ${fmt(s.total_amount, 2)}\n` +
      `monthly_average = total ÷ ${income.monthly_breakdown?.length || 1} statement month(s) = ${fmt(s.monthly_average, 2)}\n` +
      `recurring = present in ${s.months_present} month(s) ⇒ ${s.recurring ? 'YES' : 'no'}`,
    note: 'Rows below are the exact credits classified into this income source. Recurring sources feed the assessed monthly income used by the credit score.',
    columns: TXN_COLUMNS,
    rows: s.transactions || [],
  })

  return (
    <div style={{ display: 'grid', gap: 20 }}>
      {/* Headline */}
      <div className="stats-grid" style={{ marginBottom: 0 }}>
        <div className="stat-card clickable" style={{ '--accent-color': 'var(--green-dim)' }}
          onClick={() => onDrill({
            title: 'Total Income (all credits)',
            value: fmt(income.total_income, 2),
            formula: `total_income = Σ credit_amount across every credit transaction`,
            note: 'All money flowing into the account, before categorisation.',
            columns: TXN_COLUMNS,
            rows: income.sources.flatMap(s => s.transactions || []).sort((a, b) => (b.amount || 0) - (a.amount || 0)),
          })}>
          <div className="stat-label">Total Income</div>
          <div className="stat-value">{fmt(income.total_income)}</div>
          <div className="stat-sub">{income.sources.length} source categor(ies)</div>
        </div>
        <div className="stat-card" style={{ '--accent-color': 'var(--brand-dim)' }}>
          <div className="stat-label">Regular Monthly Income</div>
          <div className="stat-value">{fmt(income.regular_monthly_income)}</div>
          <div className="stat-sub">From recurring sources only</div>
        </div>
        <div className="stat-card" style={{ '--accent-color': 'var(--amber-dim)' }}>
          <div className="stat-label">Regular Income Share</div>
          <div className="stat-value">{income.regular_income_share?.toFixed(0)}%</div>
          <div className="stat-sub">Stable vs one-off inflows</div>
        </div>
      </div>

      {/* Income trend */}
      {trend.length > 0 && (
        <div className="card">
          <div className="section-title"><span>📈</span> Monthly Income Trend</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={trend} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="incFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--green)" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="var(--green)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis tickFormatter={fmtK} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} width={48} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--glass-border)', borderRadius: 8, fontSize: 12 }}
                formatter={v => [fmt(v, 2), 'Income']} labelFormatter={l => trend.find(t => t.month === l)?.full || l} />
              <Area type="monotone" dataKey="amount" stroke="var(--green)" strokeWidth={2} fill="url(#incFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Income sources — clickable */}
      <div className="card">
        <div className="section-title"><span>💰</span> Income Sources</div>
        <div className="section-sub">Click any source to see exactly which transactions were classified into it.</div>
        <div style={{ display: 'grid', gap: 10 }}>
          {income.sources.map(s => (
            <div key={s.category} className="source-card clickable" onClick={() => openSource(s)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 18 }}>{CAT_ICON[s.category] || '➕'}</span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>{s.label}</div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {s.count} txn(s) · {s.share_pct}% · avg {fmt(s.monthly_average)}/mo
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{fmt(s.total_amount)}</div>
                <span className={`chip ${s.recurring ? 'chip-accent' : ''}`} style={{ marginTop: 4 }}>
                  {s.recurring ? '🔁 Recurring' : 'One-off'}
                </span>
              </div>
              <div className="source-bar"><div style={{ width: `${(s.share_pct / maxShare) * 100}%` }} /></div>
            </div>
          ))}
        </div>
      </div>

      {/* Top payers */}
      {income.top_payers?.length > 0 && (
        <div className="card">
          <div className="section-title"><span>👥</span> Top Income Sources (Payers)</div>
          <div className="section-sub">Counterparties inferred from UPI/IMPS/NEFT narrations — verify against reference data.</div>
          <div className="data-table-wrap">
            <table className="data-table">
              <thead><tr><th>Payer</th><th className="num">Credits</th><th className="num">Total Received</th></tr></thead>
              <tbody>
                {income.top_payers.map((p, i) => (
                  <tr key={i}>
                    <td style={{ fontSize: 13 }}>{p.name}</td>
                    <td className="num mono">{p.count}</td>
                    <td className="num mono td-credit">{fmt(p.total_amount, 2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
