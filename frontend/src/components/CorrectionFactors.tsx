import { useEffect, useState } from 'react'
import { getCorrectionFactors } from '../services/pmi_dashboard'
import type { CorrectionFactor } from '../services/pmi_dashboard'
import styles from '../css/Dashboard.module.css'

export default function CorrectionFactors({ active }: { active: boolean }) {
  const [rows, setRows] = useState<CorrectionFactor[] | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [retry, setRetry] = useState(0)

  useEffect(() => {
    if (!active) return
    const controller = new AbortController()
    setLoading(true)
    setError('')
    void getCorrectionFactors(controller.signal)
      .then((response) => { if (!controller.signal.aborted) setRows(response.correction_factors) })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'Unable to load correction factors.')
      })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [active, retry])

  return (
    <section className={styles.card} aria-labelledby="correction-factors-title">
      <div className={styles.heading}>
        <div>
          <h1 id="correction-factors-title">Correction factors</h1>
          <p>The complete reference table. Discuss the factor for your case with the PMI assistant.</p>
        </div>
      </div>
      {loading && <p role="status">Loading correction factors...</p>}
      {error && <div className={styles.error} role="alert"><p>{error}</p><button className={styles.button} onClick={() => setRetry((n) => n + 1)}>Try again</button></div>}
      {rows !== null && rows.length === 0 && !loading && !error && <p className={styles.empty}>No correction factors are available.</p>}
      {rows !== null && rows.length > 0 && (
        <div className={styles.tableWrap} tabIndex={0} role="region" aria-label="Correction factors table" aria-busy={loading}>
          <table className={`${styles.table} ${styles.factors}`}>
            <caption>{rows.length} correction factors · A dash indicates no description provided.</caption>
            <thead><tr>
              <th scope="col">CF</th><th scope="col">Dry clothing or covering</th>
              <th scope="col">In air</th><th scope="col">Wet clothing, covering or body surface</th><th scope="col">Water</th>
            </tr></thead>
            <tbody>{rows.map((row) => <tr key={row.id}>
              <td className={styles.numeric}><strong>{row.cf_value}</strong></td>
              <td>{row.dry_clothing_or_covering || '—'}</td><td>{row.in_air || '—'}</td>
              <td>{row.wet_through_clothing_or_covering_or_wet_body_surface || '—'}</td><td>{row.water || '—'}</td>
            </tr>)}</tbody>
          </table>
        </div>
      )}
    </section>
  )
}
