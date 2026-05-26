const CHECK_LABELS = {
  pdf_metadata_integrity: 'PDF Metadata (CreationDate = ModDate)',
  invisible_text_overlay: 'Invisible Text Overlay',
  digital_signature: 'Digital Signature Integrity',
  balance_continuity: 'Balance Continuity',
  date_sequence_continuity: 'Date/Sequence Continuity',
  duplicate_transactions: 'Duplicate Transaction Detection',
  pixel_image_layer: 'Pixel / Image Layer Anomalies',
  pixel_image_anomaly: 'Pixel / Image Layer Anomalies',
  statistical_outlier: 'Statistical Outlier Detection',
}

export default function TamperReport({ report }) {
  if (!report) return (
    <div className="card">
      <div className="section-title"><span>🔍</span> Tamper Report</div>
      <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Tamper analysis not available (AA JSON inputs skip PDF checks).</p>
    </div>
  )

  return (
    <div style={{ display: 'grid', gap: 16 }}>
      {/* Status banner */}
      <div className={`card`} style={{
        borderColor: report.tampered ? 'var(--red)' : 'var(--green)',
        background: report.tampered ? 'var(--red-dim)' : 'var(--green-dim)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span style={{ fontSize: 36 }}>{report.tampered ? '🚫' : '✅'}</span>
          <div>
            <div style={{ fontWeight: 700, fontSize: 18, color: report.tampered ? 'var(--red)' : 'var(--green)' }}>
              {report.tampered ? 'TAMPER DETECTED' : 'INTEGRITY VERIFIED'}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              {report.checks_failed?.length || 0} check(s) failed · {report.checks_passed?.length || 0} check(s) passed
            </div>
          </div>
        </div>
      </div>

      {/* Failed checks */}
      {report.checks_failed?.length > 0 && (
        <div className="card">
          <div className="section-title"><span>❌</span> Failed Checks</div>
          {report.checks_failed.map((c, i) => (
            <div key={i} style={{ marginBottom: 16 }}>
              <div className="check-row">
                <div className="check-dot check-dot-fail" />
                <strong style={{ fontSize: 13 }}>{CHECK_LABELS[c.check] || c.check}</strong>
              </div>
              <div style={{ marginLeft: 18, fontSize: 12, color: 'var(--amber)', padding: '8px 12px',
                background: 'var(--amber-dim)', borderRadius: 6, marginBottom: 8 }}>
                {c.detail}
              </div>
              {c.rows_affected?.length > 0 && (
                <div style={{ marginLeft: 18 }}>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6 }}>
                    Affected rows ({c.rows_affected.length}):
                  </div>
                  <div className="data-table-wrap" style={{ maxHeight: 180, overflowY: 'auto' }}>
                    <table className="data-table">
                      <thead>
                        <tr>
                          {Object.keys(c.rows_affected[0] || {}).slice(0, 5).map(k => <th key={k}>{k}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {c.rows_affected.slice(0, 20).map((r, ri) => (
                          <tr key={ri}>
                            {Object.values(r).slice(0, 5).map((v, vi) => (
                              <td key={vi} className="mono" style={{ fontSize: 11 }}>{String(v ?? '—').slice(0, 60)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Passed checks */}
      {report.checks_passed?.length > 0 && (
        <div className="card">
          <div className="section-title"><span>✅</span> Passed Checks</div>
          {report.checks_passed.map((c, i) => (
            <div key={i} className="check-row">
              <div className="check-dot check-dot-pass" />
              <span style={{ fontSize: 13 }}>{CHECK_LABELS[c] || c}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
