import { useEffect } from 'react'

const fmtAmt = n => n == null ? '—' : `₹${Number(n).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`

function renderCell(row, col) {
  const v = row[col.key]
  if (col.type === 'amount') return <span className="mono">{fmtAmt(v)}</span>
  if (col.type === 'credit') return <span className="mono td-credit">{v != null ? fmtAmt(v) : '—'}</span>
  if (col.type === 'debit')  return <span className="mono td-debit">{v != null ? fmtAmt(v) : '—'}</span>
  if (col.type === 'date')   return <span className="mono">{v || '—'}</span>
  return <span style={{ fontSize: 12 }}>{v == null || v === '' ? '—' : String(v)}</span>
}

/**
 * Generic provenance modal.
 * detail = {
 *   title, subtitle,
 *   formula,            // string — how the value was derived
 *   note,               // optional explanatory text
 *   value,              // optional headline value (string)
 *   columns: [{ key, label, type, align }],
 *   rows: [...],        // reference / contributing transactions
 *   emptyText
 * }
 */
export default function DrillDownModal({ detail, onClose }) {
  useEffect(() => {
    const onKey = e => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => { window.removeEventListener('keydown', onKey); document.body.style.overflow = '' }
  }, [onClose])

  if (!detail) return null
  const { title, subtitle, formula, note, value, columns = [], rows = [], emptyText } = detail

  const total = rows.reduce((s, r) => {
    const a = r.amount ?? r.credit_amount ?? r.debit_amount ?? 0
    return s + (Number(a) || 0)
  }, 0)

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <div className="modal-title">{title}</div>
            {subtitle && <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 3 }}>{subtitle}</div>}
          </div>
          {value != null && (
            <div style={{ marginLeft: 16, textAlign: 'right' }}>
              <div style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Value</div>
              <div style={{ fontSize: 20, fontWeight: 800, letterSpacing: '-0.3px' }}>{value}</div>
            </div>
          )}
          <button className="modal-close" onClick={onClose} aria-label="Close">×</button>
        </div>

        <div className="modal-body">
          {formula && (
            <div className="derivation">
              <div className="derivation-label">How this was derived</div>
              <div className="derivation-formula">{formula}</div>
              {note && <div className="derivation-note">{note}</div>}
            </div>
          )}
          {!formula && note && <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>{note}</p>}

          {columns.length > 0 && (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                <span className="section-title" style={{ margin: 0, fontSize: 13 }}>
                  <span>📑</span> Reference data ({rows.length})
                </span>
                {rows.length > 0 && total > 0 && (
                  <span className="chip chip-accent">Σ {fmtAmt(total)}</span>
                )}
              </div>
              {rows.length === 0 ? (
                <p style={{ color: 'var(--text-muted)', fontSize: 13, padding: '12px 0' }}>{emptyText || 'No contributing rows.'}</p>
              ) : (
                <div className="data-table-wrap" style={{ maxHeight: 420, overflowY: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>{columns.map(c => <th key={c.key} className={c.align === 'right' ? 'num' : ''}>{c.label}</th>)}</tr>
                    </thead>
                    <tbody>
                      {rows.map((row, i) => (
                        <tr key={i}>
                          {columns.map(c => (
                            <td key={c.key} className={c.align === 'right' ? 'num' : ''}>{renderCell(row, c)}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}
