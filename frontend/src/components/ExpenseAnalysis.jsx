import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const fmt = (n, d = 0) => n == null ? '—' : `₹${Number(n).toLocaleString('en-IN', { minimumFractionDigits: d, maximumFractionDigits: d })}`
const fmtK = n => `₹${(n / 1000).toFixed(0)}k`

const CAT_ICON = {
  EMI: '🏦', CC: '💳', INSURANCE: '🛡️', INVEST: '📈', RENT_PAID: '🏠',
  UTILITY: '💡', TAX: '🧾', DISBURSAL: '🏧', EDUCATION: '🎓',
  SUBSCRIPTION: '📺', OD: '⚠️', PAYROLL: '👥', SUPPLIER: '📦',
  MFI: '🤝', KCC: '🌾', COOP_SHARE: '🏛️',
  ATM: '🏧', POS: '🛒', UPI: '📱', CASH: '💵', CHEQUE: '🧾',
  TRANSFER: '🔁', DD_SWEEP: '💱', AEPS: '👆', OTHER: '➖',
}

const TXN_COLUMNS = [
  { key: 'date', label: 'Date', type: 'date' },
  { key: 'narration', label: 'Narration', type: 'text' },
  { key: 'mode', label: 'Mode', type: 'text' },
  { key: 'amount', label: 'Amount', type: 'debit', align: 'right' },
]

export default function ExpenseAnalysis({ expense, onDrill }) {
  if (!expense || !expense.categories?.length) return (
    <div className="card">
      <div className="section-title"><span>💸</span> Expense Analysis</div>
      <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>No debit transactions available to categorise.</p>
    </div>
  )

  const maxShare = Math.max(...expense.categories.map(c => c.share_pct || 0), 1)
  const trend = (expense.monthly_breakdown || []).map(m => ({ month: m.month?.slice(5), full: m.month, amount: m.amount }))

  const openCat = (c) => onDrill({
    title: c.label,
    subtitle: `${c.count} debit(s) · ${c.is_fixed_obligation ? 'Fixed obligation (counts in FOIR)' : c.recurring ? 'Recurring' : 'One-off'} · ${c.share_pct}% of spend`,
    value: fmt(c.total_amount, 2),
    formula:
      `category = master narration lexicon match (purpose > channel)\n` +
      `total = Σ debit_amount of ${c.count} matched txn(s) = ${fmt(c.total_amount, 2)}\n` +
      `monthly_average = total ÷ ${expense.monthly_breakdown?.length || 1} month(s) = ${fmt(c.monthly_average, 2)}\n` +
      `fixed_obligation = ${c.is_fixed_obligation ? 'YES → included in FOIR' : 'no'}`,
    note: 'Rows below are the exact debits classified into this category by the narration lexicon.',
    columns: TXN_COLUMNS,
    rows: c.transactions || [],
  })

  return (
    <div style={{ display: 'grid', gap: 20 }}>
      <div className="stats-grid" style={{ marginBottom: 0 }}>
        <div className="stat-card clickable" style={{ '--accent-color': 'var(--red-dim)' }}
          onClick={() => onDrill({
            title: 'Total Expense (all debits)', value: fmt(expense.total_expense, 2),
            formula: `total_expense = Σ debit_amount across every debit transaction`,
            note: 'All outflows before categorisation.',
            columns: TXN_COLUMNS,
            rows: expense.categories.flatMap(c => c.transactions || []).sort((a, b) => (b.amount || 0) - (a.amount || 0)),
          })}>
          <div className="stat-label">Total Expense</div>
          <div className="stat-value">{fmt(expense.total_expense)}</div>
          <div className="stat-sub">{expense.categories.length} categor(ies)</div>
        </div>
        <div className="stat-card" style={{ '--accent-color': 'var(--amber-dim)' }}>
          <div className="stat-label">Monthly Fixed Obligations</div>
          <div className="stat-value">{fmt(expense.monthly_obligations)}</div>
          <div className="stat-sub">EMI + CC + insurance + rent + MFI…</div>
        </div>
        <div className="stat-card" style={{ '--accent-color': 'var(--brand-dim)' }}>
          <div className="stat-label">Fixed Obligation Share</div>
          <div className="stat-value">{expense.fixed_obligation_share?.toFixed(0)}%</div>
          <div className="stat-sub">Committed vs discretionary spend</div>
        </div>
      </div>

      {trend.length > 0 && (
        <div className="card">
          <div className="section-title"><span>📉</span> Monthly Expense Trend</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={trend} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
              <defs>
                <linearGradient id="expFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="var(--red)" stopOpacity={0.5} />
                  <stop offset="100%" stopColor="var(--red)" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="month" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
              <YAxis tickFormatter={fmtK} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} width={48} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--glass-border)', borderRadius: 8, fontSize: 12 }}
                formatter={v => [fmt(v, 2), 'Expense']} labelFormatter={l => trend.find(t => t.month === l)?.full || l} />
              <Area type="monotone" dataKey="amount" stroke="var(--red)" strokeWidth={2} fill="url(#expFill)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="card">
        <div className="section-title"><span>💸</span> Expense Categories</div>
        <div className="section-sub">Classified by the master narration lexicon. Obligations marked with a shield count toward FOIR.</div>
        <div style={{ display: 'grid', gap: 10 }}>
          {expense.categories.map(c => (
            <div key={c.category} className="source-card clickable" onClick={() => openCat(c)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <span style={{ fontSize: 18 }}>{CAT_ICON[c.category] || '➖'}</span>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14 }}>
                    {c.label}
                    {c.is_fixed_obligation && <span title="Counts toward FOIR" style={{ marginLeft: 6 }}>🛡️</span>}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                    {c.count} txn(s) · {c.share_pct}% · avg {fmt(c.monthly_average)}/mo
                  </div>
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums', color: 'var(--red)' }}>{fmt(c.total_amount)}</div>
                {c.is_fixed_obligation && <span className="chip chip-accent" style={{ marginTop: 4 }}>Obligation</span>}
              </div>
              <div className="source-bar"><div style={{ width: `${(c.share_pct / maxShare) * 100}%`, background: 'linear-gradient(90deg, var(--red), var(--amber))' }} /></div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
