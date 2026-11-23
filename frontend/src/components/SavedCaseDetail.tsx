import type { SavedCase } from '../services/pmi_dashboard'
import { areaLabel, isRecord, measurementLabel, readableLabel, savedDate, savedMethodName } from '../utils/pmiDisplay'
import styles from '../css/Dashboard.module.css'

export default function SavedCaseDetail({ item, onBack }: { item: SavedCase; onBack: () => void }) {
  const data = item.input_data
  const checks = isRecord(data.exclusion_criteria) ? Object.entries(data.exclusion_criteria).filter(([, value]) => value != null) : []
  const caseFields = [
    ['Rectal temperature', measurementLabel(data.rectal_temperature_c, '°C')],
    ['Ambient temperature', measurementLabel(data.ambient_temperature_c, '°C')],
    ['Body weight', measurementLabel(data.body_mass_kg, 'kg')],
    ['Correction factor', measurementLabel(data.correction_factor)],
    ['Age', measurementLabel(data.age, 'years')],
    ['Subject origin', areaLabel(data.subject_area)],
    ['Time gap', measurementLabel(data.time_gap_minutes, 'min')],
  ]
  const biologicalFields = [
    ['Potassium (K+)', measurementLabel(data.potassium, 'mmol/L')],
    ['Hypoxanthine (Hx)', measurementLabel(data.hypoxanthine, 'mmol/L')],
    [isRecord(data.u_am) && data.u_am.analyte === 'urea' ? 'Urea' : isRecord(data.u_am) && data.u_am.analyte === 'ammonium' ? 'Ammonium' : 'U/Am', measurementLabel(data.u_am)],
    ['Albumin', measurementLabel(data.albumin)],
  ]
  const acknowledged = item.evaluation_snapshot?.result_selection?.acknowledged_warning_method_ids ?? []

  return (
    <section className={styles.card} aria-labelledby="case-detail-title">
      <div className={styles.heading}>
        <div><h1 id="case-detail-title">Case #{item.calculation_id}</h1><p>Saved {savedDate(item.created_at)}</p></div>
        <button className={`${styles.button} ${styles.secondary}`} onClick={onBack}>Back to saved cases</button>
      </div>

      <section className={styles.detailSection} aria-labelledby="saved-results-title">
        <h2 id="saved-results-title">Estimated PMI <span className={styles.muted}>(hh:mm)</span></h2>
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead><tr><th scope="col">Method</th><th scope="col">PMI</th><th scope="col">Applicability notes</th></tr></thead>
            <tbody>{item.saved_results.map((result) => {
              const evaluation = item.evaluation_snapshot?.evaluated_results?.find((r) => r.method_id === result.method_name)
              const warnings = evaluation?.checks.filter((c) => ['failed', 'unknown'].includes(c.outcome)
                && !(evaluation.method_kind === 'henssge' && c.id === 'scientific_applicability')) ?? []
              return <tr key={result.method_name}>
                <td><strong>{savedMethodName(item, result.method_name)}</strong><div className={styles.muted}>Version {result.method_version}</div></td>
                <td className={styles.numeric}>{result.pmi_value}</td>
                <td>{warnings.length > 0 ? <>
                  {acknowledged.includes(result.method_name) && <p className={styles.badge}>Warnings acknowledged</p>}
                  <details className={styles.notes}><summary>View {warnings.length} applicability note(s)</summary>
                    <ul>{warnings.map((c) => <li key={c.id}><strong>{c.outcome === 'failed' ? 'Not met' : 'Not verified'}:</strong> {c.message}</li>)}</ul>
                  </details>
                </> : '—'}</td>
              </tr>
            })}</tbody>
          </table>
        </div>
        <p className={styles.muted}>Henssge is relative to temperature measurement. Where supplied, the time gap is already included in biological estimates.</p>
      </section>

      <section className={styles.detailSection} aria-labelledby="saved-median-title">
        <h2 id="saved-median-title">Median PMI</h2>
        {item.median_pmi === null ? <p>Not calculated.</p> : <>
          <p><strong className={styles.numeric}>{item.median_pmi}</strong> (hh:mm)</p>
          <p>Methods: {item.median_selected_methods.map((id) => savedMethodName(item, id)).join(', ')}.</p>
          {(item.evaluation_snapshot?.median_result?.acknowledged_warning_method_ids?.length ?? 0) > 0 &&
            <p className={styles.muted}>Applicability warnings were acknowledged for the median selection.</p>}
        </>}
      </section>

      <section className={styles.detailSection} aria-labelledby="saved-input-title"><h2 id="saved-input-title">Case data</h2>
        <dl className={styles.dataGrid}>{caseFields.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
        {isRecord(data.correction_factor_context) && typeof data.correction_factor_context.description === 'string' &&
          <p className={styles.muted}>Correction factor context: {data.correction_factor_context.description}</p>}
      </section>
      <section className={styles.detailSection} aria-labelledby="saved-biology-title"><h2 id="saved-biology-title">Biochemical analyses</h2>
        <dl className={styles.dataGrid}>{biologicalFields.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
      </section>
      <section className={styles.detailSection} aria-labelledby="saved-exclusions-title"><h2 id="saved-exclusions-title">Exclusion criteria</h2>
        {checks.length === 0 ? <p className={styles.muted}>No exclusion criteria were provided.</p> :
          <dl className={styles.dataGrid}>{checks.map(([key, value]) => <div key={key}><dt>{readableLabel(key)}</dt><dd>{typeof value === 'string' ? readableLabel(value) : 'Unknown'}</dd></div>)}</dl>}
      </section>
    </section>
  )
}
