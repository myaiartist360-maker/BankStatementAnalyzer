import { useState, useMemo } from 'react'

const GAMBLING_KEYWORDS = ['DREAM11','MPL','MY11CIRCLE','FANTASY','BETWAY','ADDA52','WINZO','ZUPEE','CASINO','RUMMY','POKER','BETFAIR','HOWZAT']
const CRYPTO_KEYWORDS   = ['WAZIRX','COINDCX','ZEBPAY','BITBNS','BINANCE','COINSWITCH']

function rowClass(txn) {
  const narr = (txn.narration || '').toUpperCase()
  if (GAMBLING_KEYWORDS.some(k => narr.includes(k))) return 'td-gambling'
  if (txn.is_reversal) return 'td-reversal'
  if (txn.credit_amount != null) return 'td-credit'
  return 'td-debit'
}

function ModeTag({ mode }) {
  const colors = {
    UPI: 'var(--brand)', NEFT: 'var(--cyan)', RTGS: 'var(--cyan)',
    IMPS: 'var(--green)', NACH: 'var(--amber)', ECS: 'var(--amber)',
    ATM: 'var(--red)', CHEQUE: 'var(--purple)', POS: 'var(--text-secondary)',
    CASH: 'var(--red)', INTEREST: 'var(--green)', CHARGES: 'var(--text-muted)',
    SI: 'var(--amber)', OTHER: 'var(--text-muted)',
  }
  return (
    <span style={{ fontSize: 10, fontWeight: 700, color: colors[mode] || 'var(--text-muted)',
      background: (colors[mode] || 'var(--text-muted)') + '22', padding: '2px 6px',
      borderRadius: 4, fontFamily: 'JetBrains Mono, monospace' }}>
      {mode}
    </span>
  )
}

const MODES = ['ALL','UPI','NEFT','RTGS','IMPS','NACH','ECS','ATM','CHEQUE','CASH','INTEREST','CHARGES','OTHER']

export default function TransactionTable({ transactions }) {
  const [filter, setFilter] = useState('ALL')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(0)
  const PAGE_SIZE = 50

  const filtered = useMemo(() => {
    let list = transactions
    if (filter !== 'ALL') list = list.filter(t => t.transaction_mode === filter)
    if (search.trim()) {
      const q = search.trim().toLowerCase()
      list = list.filter(t => (t.narration || '').toLowerCase().includes(q) || (t.date || '').includes(q))
    }
    return list
  }, [transactions, filter, search])

  const page_data = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const total_pages = Math.ceil(filtered.length / PAGE_SIZE)

  return (
    <div>
      {/* Filters */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <input className="form-input" style={{ maxWidth: 220, padding: '8px 12px' }}
          placeholder="Search narration…" value={search} onChange={e => { setSearch(e.target.value); setPage(0) }} />
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {MODES.map(m => (
            <button key={m} onClick={() => { setFilter(m); setPage(0) }}
              className={`btn btn-sm ${filter === m ? 'btn-primary' : 'btn-secondary'}`}>
              {m}
            </button>
          ))}
        </div>
        <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 'auto' }}>
          {filtered.length} rows
        </span>
      </div>

      {/* Table */}
      <div className="data-table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th><th>Narration</th><th>Mode</th>
              <th style={{ textAlign: 'right' }}>Debit (₹)</th>
              <th style={{ textAlign: 'right' }}>Credit (₹)</th>
              <th style={{ textAlign: 'right' }}>Balance (₹)</th>
              <th>Flag</th>
            </tr>
          </thead>
          <tbody>
            {page_data.length === 0 && (
              <tr><td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px 0' }}>No transactions match</td></tr>
            )}
            {page_data.map((t, i) => {
              const cls = rowClass(t)
              const narr = (t.narration || '').toUpperCase()
              const isGambling = GAMBLING_KEYWORDS.some(k => narr.includes(k))
              const isCrypto   = CRYPTO_KEYWORDS.some(k => narr.includes(k))
              return (
                <tr key={i}>
                  <td className="mono" style={{ whiteSpace: 'nowrap' }}>{t.date}</td>
                  <td style={{ maxWidth: 320, fontSize: 12 }}>
                    <span title={t.narration}>{t.narration?.slice(0, 60)}{t.narration?.length > 60 ? '…' : ''}</span>
                  </td>
                  <td><ModeTag mode={t.transaction_mode || 'OTHER'} /></td>
                  <td className={`mono ${t.debit_amount != null ? 'td-debit' : ''}`} style={{ textAlign: 'right' }}>
                    {t.debit_amount != null ? t.debit_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : ''}
                  </td>
                  <td className={`mono ${t.credit_amount != null ? 'td-credit' : ''}`} style={{ textAlign: 'right' }}>
                    {t.credit_amount != null ? t.credit_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : ''}
                  </td>
                  <td className="mono" style={{ textAlign: 'right', fontSize: 11, color: 'var(--text-secondary)' }}>
                    {t.closing_balance != null ? t.closing_balance.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '—'}
                  </td>
                  <td>
                    {t.is_reversal && <span className="badge badge-warning" style={{ marginRight: 4 }}>↩ REV</span>}
                    {isGambling   && <span className="badge badge-purple">🎲</span>}
                    {isCrypto     && <span className="badge badge-info">₿</span>}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {total_pages > 1 && (
        <div style={{ display: 'flex', gap: 8, marginTop: 16, alignItems: 'center', justifyContent: 'flex-end' }}>
          <button className="btn btn-secondary btn-sm" disabled={page === 0} onClick={() => setPage(p => p - 1)}>← Prev</button>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Page {page + 1} / {total_pages}</span>
          <button className="btn btn-secondary btn-sm" disabled={page >= total_pages - 1} onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      )}
    </div>
  )
}
