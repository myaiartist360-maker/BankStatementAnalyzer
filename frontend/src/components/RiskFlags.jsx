const SEV_ICON = { HIGH: '🔴', MEDIUM: '🟡', LOW: '🔵' }
const SEV_ORDER = { HIGH: 0, MEDIUM: 1, LOW: 2 }

function FlagCard({ flag }) {
  return (
    <div className={`flag-card flag-${flag.severity}`}>
      <div className="flag-icon">{SEV_ICON[flag.severity]}</div>
      <div>
        <div className="flag-title">{flag.flag.replace(/_/g, ' ')}</div>
        <div className="flag-detail">{flag.detail}</div>
      </div>
      <span className={`badge badge-${flag.severity === 'HIGH' ? 'danger' : flag.severity === 'MEDIUM' ? 'warning' : 'info'}`} style={{ marginLeft: 'auto', flexShrink: 0 }}>
        {flag.severity}
      </span>
    </div>
  )
}

const fmt = n => n != null ? `₹${Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'

export default function RiskFlags({ flags, gambling, crypto, roundTrip, hvcash }) {
  const sorted = [...(flags || [])].sort((a, b) => SEV_ORDER[a.severity] - SEV_ORDER[b.severity])

  return (
    <div style={{ display: 'grid', gap: 20 }}>
      {/* Flags */}
      <div className="card">
        <div className="section-title"><span>🚨</span> High-Risk Flags ({sorted.length})</div>
        {sorted.length === 0 ? (
          <div style={{ color: 'var(--green)', fontSize: 14, textAlign: 'center', padding: '24px 0' }}>✅ No high-risk flags detected</div>
        ) : sorted.map((f, i) => <FlagCard key={i} flag={f} />)}
      </div>

      {/* Gambling breakdown */}
      {gambling?.count > 0 && (
        <div className="card">
          <div className="section-title"><span>🎲</span> Gambling Transactions</div>
          <div style={{ marginBottom: 16, display: 'flex', gap: 20 }}>
            <div><span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Count</span><br/><strong>{gambling.count}</strong></div>
            <div><span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Total</span><br/><strong style={{ color: 'var(--red)' }}>{fmt(gambling.total_amount)}</strong></div>
          </div>
          <div className="data-table-wrap" style={{ maxHeight: 240, overflowY: 'auto' }}>
            <table className="data-table">
              <thead><tr><th>Date</th><th>Narration</th><th>Amount</th></tr></thead>
              <tbody>
                {gambling.instances.map((g, i) => (
                  <tr key={i}>
                    <td className="mono">{g.date}</td>
                    <td style={{ fontSize: 12 }}>{g.narration}</td>
                    <td className="mono td-debit" style={{ textAlign: 'right' }}>{fmt(g.amount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Crypto */}
      {crypto?.count > 0 && (
        <div className="card">
          <div className="section-title"><span>₿</span> Crypto Transactions</div>
          <div style={{ display: 'flex', gap: 20 }}>
            <div><span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Count</span><br/><strong>{crypto.count}</strong></div>
            <div><span style={{ color: 'var(--text-muted)', fontSize: 12 }}>Total</span><br/><strong style={{ color: 'var(--amber)' }}>{fmt(crypto.total_amount)}</strong></div>
          </div>
        </div>
      )}

      {/* Round-trip */}
      {roundTrip?.count > 0 && (
        <div className="card">
          <div className="section-title"><span>🔄</span> Round-Trip Fund Cycling</div>
          <div style={{ marginBottom: 12 }}><strong>{roundTrip.count}</strong> pair(s) detected</div>
          <div className="data-table-wrap" style={{ maxHeight: 220, overflowY: 'auto' }}>
            <table className="data-table">
              <thead><tr><th>Credit Date</th><th>Debit Date</th><th>Amount</th><th>Credit Narration</th><th>Debit Narration</th></tr></thead>
              <tbody>
                {roundTrip.instances.map((r, i) => (
                  <tr key={i}>
                    <td className="mono">{r.credit_date}</td>
                    <td className="mono">{r.debit_date}</td>
                    <td className="mono td-debit">{fmt(r.amount)}</td>
                    <td style={{ fontSize: 11 }}>{r.credit_narration?.slice(0, 40)}</td>
                    <td style={{ fontSize: 11 }}>{r.debit_narration?.slice(0, 40)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* High-value cash */}
      {hvcash?.count > 0 && (
        <div className="card">
          <div className="section-title"><span>💵</span> High-Value Cash Withdrawals</div>
          <div style={{ marginBottom: 12 }}>{hvcash.count} day(s) · Total: <strong style={{ color: 'var(--red)' }}>{fmt(hvcash.total_amount)}</strong></div>
          {hvcash.instances.map((d, i) => (
            <div key={i} style={{ padding: '10px 0', borderBottom: '1px solid var(--glass-border)', fontSize: 13 }}>
              <span className="mono">{d.date}</span> — <strong>{fmt(d.total_amount)}</strong>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
