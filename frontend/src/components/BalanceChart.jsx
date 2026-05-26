import { useMemo } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ResponsiveContainer } from 'recharts'

const MAB = 10_000

function buildEodSeries(transactions) {
  if (!transactions.length) return []
  const dateBalance = {}
  for (const t of transactions) {
    if (t.date && t.closing_balance != null) {
      dateBalance[t.date] = t.closing_balance
    }
  }

  const dates = Object.keys(dateBalance).sort()
  if (!dates.length) return []

  // Carry forward
  const series = []
  let last = null
  let cur = new Date(dates[0])
  const end = new Date(dates[dates.length - 1])

  while (cur <= end) {
    const d = cur.toISOString().slice(0, 10)
    if (d in dateBalance) last = dateBalance[d]
    if (last !== null) series.push({ date: d, balance: last, belowMab: last < MAB })
    cur.setDate(cur.getDate() + 1)
  }
  return series
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  const val = payload[0].value
  return (
    <div style={{ background: 'var(--bg-card)', border: '1px solid var(--glass-border)', borderRadius: 8, padding: '10px 14px' }}>
      <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 15, fontWeight: 700, color: val < MAB ? 'var(--red)' : 'var(--green)' }}>
        ₹{val.toLocaleString('en-IN')}
      </div>
    </div>
  )
}

export default function BalanceChart({ transactions }) {
  const series = useMemo(() => buildEodSeries(transactions), [transactions])

  if (!series.length) return (
    <div className="card">
      <div className="section-title"><span>📈</span> Balance Timeline</div>
      <div style={{ color: 'var(--text-muted)', fontSize: 13, textAlign: 'center', padding: '32px 0' }}>No balance data available</div>
    </div>
  )

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div className="section-title" style={{ margin: 0 }}><span>📈</span> Daily EOD Balance</div>
        <div style={{ display: 'flex', gap: 16, fontSize: 11 }}>
          <span style={{ color: 'var(--green)' }}>● Above MAB</span>
          <span style={{ color: 'var(--red)' }}>● Below ₹10,000</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={240}>
        <LineChart data={series} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis dataKey="date" tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
            tickFormatter={v => v.slice(5)} interval="preserveStartEnd" />
          <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }}
            tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} width={52} />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine y={MAB} stroke="var(--red)" strokeDasharray="4 4" strokeOpacity={0.5} />
          <Line type="monotone" dataKey="balance" stroke="var(--brand)" strokeWidth={2}
            dot={false} activeDot={{ r: 4, fill: 'var(--brand)' }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
