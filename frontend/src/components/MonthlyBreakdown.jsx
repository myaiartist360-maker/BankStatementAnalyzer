import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { useMemo } from 'react'

const fmt = n => `₹${(n / 1000).toFixed(1)}k`

export default function MonthlyBreakdown({ credits, debits }) {
  const data = useMemo(() => {
    const months = new Set([...credits.map(c => c.month), ...debits.map(d => d.month)])
    const creditMap = Object.fromEntries(credits.map(c => [c.month, c.amount]))
    const debitMap  = Object.fromEntries(debits.map(d => [d.month, d.amount]))
    return [...months].sort().map(m => ({
      month: m.slice(5), // MM only
      fullMonth: m,
      credits: creditMap[m] || 0,
      debits: debitMap[m] || 0,
    }))
  }, [credits, debits])

  if (!data.length) return null

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--glass-border)', borderRadius: 8, padding: '10px 14px' }}>
        <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>{payload[0]?.payload?.fullMonth}</div>
        {payload.map((p, i) => (
          <div key={i} style={{ fontSize: 13, color: p.fill, fontWeight: 600 }}>
            {p.name}: ₹{Number(p.value).toLocaleString('en-IN')}
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="card">
      <div className="section-title"><span>📅</span> Monthly Credit vs Debit</div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} margin={{ top: 4, right: 16, bottom: 0, left: 0 }} barCategoryGap="30%">
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="month" tick={{ fill: 'var(--text-muted)', fontSize: 11 }} />
          <YAxis tickFormatter={fmt} tick={{ fill: 'var(--text-muted)', fontSize: 10 }} width={52} />
          <Tooltip content={<CustomTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-secondary)' }} />
          <Bar dataKey="credits" name="Credits" fill="var(--green)" radius={[3,3,0,0]} fillOpacity={0.85} />
          <Bar dataKey="debits"  name="Debits"  fill="var(--red)"   radius={[3,3,0,0]} fillOpacity={0.85} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
