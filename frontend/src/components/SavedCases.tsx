import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { deleteSavedCase, emptyHistoryFilters, getHistory, getHistoryMethods } from '../services/pmi_dashboard'
import type { HistoryFilters, HistoryMethod, HistoryResponse, SavedCase } from '../services/pmi_dashboard'
import { areaLabel, readableLabel, savedDate, savedMethodName, subjectAreas } from '../utils/pmiDisplay'
import SavedCaseDetail from './SavedCaseDetail'
import styles from '../css/Dashboard.module.css'

export default function SavedCases({ active, revision }: { active: boolean; revision: number }) {
  const [filters, setFilters] = useState<HistoryFilters>({ ...emptyHistoryFilters })
  const [query, setQuery] = useState({ filters: { ...emptyHistoryFilters }, offset: 0 })
  const [response, setResponse] = useState<HistoryResponse | null>(null)
  const [methods, setMethods] = useState<HistoryMethod[]>([])
  const [error, setError] = useState('')
  const [validationError, setValidationError] = useState('')
  const [methodsError, setMethodsError] = useState('')
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<SavedCase | null>(null)
  const [retry, setRetry] = useState(0)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deleteError, setDeleteError] = useState('')
  const [deleteNotice, setDeleteNotice] = useState('')
  const deletingRef = useRef(false)

  useEffect(() => {
    if (!active) return
    const controller = new AbortController()
    setLoading(true)
    setError('')
    void getHistory(query.filters, query.offset, controller.signal)
      .then((result) => {
        if (controller.signal.aborted) return
        if (result.total > 0 && result.offset >= result.total) {
          setQuery((previous) => ({ ...previous, offset: Math.floor((result.total - 1) / result.limit) * result.limit }))
        } else setResponse(result)
      })
      .catch((cause: unknown) => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'Unable to load saved cases.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [active, query, revision, retry])

  useEffect(() => {
    if (!active) return
    const controller = new AbortController()
    setMethodsError('')
    void getHistoryMethods(controller.signal)
      .then((result) => { if (!controller.signal.aborted) setMethods(result.methods) })
      .catch(() => { if (!controller.signal.aborted) setMethodsError('Method options could not be loaded. Use Refresh to retry.') })
    return () => controller.abort()
  }, [active, revision, retry])

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (filters.dateFrom && filters.dateTo && filters.dateFrom > filters.dateTo) {
      setValidationError('The end date must be on or after the start date.')
      return
    }
    setValidationError('')
    setSelected(null)
    setQuery({ filters: { ...filters }, offset: 0 })
  }

  function update<K extends keyof HistoryFilters>(key: K, value: HistoryFilters[K]) {
    setFilters((previous) => ({ ...previous, [key]: value }))
  }

  function resetFilters() {
    setValidationError('')
    setFilters({ ...emptyHistoryFilters })
    setQuery({ filters: { ...emptyHistoryFilters }, offset: 0 })
    setSelected(null)
  }

  async function removeCase(item: SavedCase) {
    if (deletingRef.current) return
    if (!window.confirm(`Permanently delete case #${item.calculation_id}? Its saved results and median will also be deleted. This cannot be undone.`)) return
    deletingRef.current = true
    setDeletingId(item.calculation_id)
    setDeleteError('')
    setDeleteNotice('')
    try {
      await deleteSavedCase(item.calculation_id)
      setResponse((previous) => previous ? {
        ...previous, total: previous.calculations.some((row) => row.calculation_id === item.calculation_id)
          ? Math.max(0, previous.total - 1) : previous.total,
        calculations: previous.calculations.filter((row) => row.calculation_id !== item.calculation_id),
      } : previous)
      setDeleteNotice(`Case #${item.calculation_id} was deleted.`)
      setRetry((value) => value + 1)
    } catch (cause) {
      setDeleteError(cause instanceof Error ? cause.message : 'Unable to delete the saved case.')
    } finally {
      deletingRef.current = false
      setDeletingId(null)
    }
  }

  if (selected) return <SavedCaseDetail item={selected} onBack={() => setSelected(null)} />

  return (
    <section className={styles.card} aria-labelledby="saved-cases-title">
      <div className={styles.heading}>
        <div><h1 id="saved-cases-title">Saved cases</h1><p>Review your saved case data, results and optional median.</p></div>
        <button className={`${styles.button} ${styles.secondary}`} disabled={loading} onClick={() => setRetry((n) => n + 1)}>Refresh</button>
      </div>
      <form className={styles.filters} onSubmit={applyFilters} aria-label="Search saved cases">
        <label>Case ID<input type="number" min="1" step="1" placeholder="e.g. 42" value={filters.caseId} onChange={(e) => update('caseId', e.target.value)} /></label>
        <label>Saved from<input type="date" value={filters.dateFrom} onChange={(e) => update('dateFrom', e.target.value)} /></label>
        <label>Saved to<input type="date" value={filters.dateTo} min={filters.dateFrom || undefined} onChange={(e) => update('dateTo', e.target.value)} /></label>
        <label>Method<select value={filters.method} onChange={(e) => update('method', e.target.value)}>
          <option value="">All methods</option>{methods.map((m) => <option key={m.method_id} value={m.method_id}>{m.label}</option>)}
          {filters.method && !methods.some((m) => m.method_id === filters.method) && <option value={filters.method}>{readableLabel(filters.method)}</option>}
        </select></label>
        <label>Subject origin<select value={filters.subjectArea} onChange={(e) => update('subjectArea', e.target.value)}>
          <option value="">All origins</option>{subjectAreas.map(([id, label]) => <option key={id} value={id}>{label}</option>)}
        </select></label>
        <label>Median<select value={filters.median} onChange={(e) => update('median', e.target.value as HistoryFilters['median'])}>
          <option value="">All cases</option><option value="true">Calculated</option><option value="false">Not calculated</option>
        </select></label>
        <label>Sort by<select value={filters.sort} onChange={(e) => update('sort', e.target.value as HistoryFilters['sort'])}>
          <option value="newest">Newest first</option><option value="oldest">Oldest first</option>
        </select></label>
        <div className={styles.filterActions}><button className={styles.button} type="submit">Apply filters</button><button className={`${styles.button} ${styles.secondary}`} type="button" onClick={resetFilters}>Reset</button></div>
      </form>
      {validationError && <p className={styles.error} role="alert">{validationError}</p>}
      {methodsError && <p className={styles.error} role="alert">{methodsError}</p>}
      {error && <p className={styles.error} role="alert">{error}</p>}
      {deleteError && <p className={styles.error} role="alert">{deleteError}</p>}
      {deleteNotice && <p role="status">{deleteNotice}</p>}
      {deletingId !== null && <p role="status">Deleting case #{deletingId}...</p>}
      {loading && <p role="status">Loading saved cases...</p>}
      {response && !loading && !error && (
        response.calculations.length === 0 ? <p className={styles.empty}>No saved cases match these filters.</p> : <>
          <div className={styles.tableWrap} tabIndex={0} role="region" aria-label="Saved cases table">
            <table className={styles.table}>
              <thead><tr><th scope="col">Case</th><th scope="col">Saved on</th><th scope="col">Subject origin</th><th scope="col">Methods kept</th><th scope="col">Median (hh:mm)</th><th scope="col">Actions</th></tr></thead>
              <tbody>{response.calculations.map((item) => <tr key={item.calculation_id}>
                <td className={styles.numeric}><strong>#{item.calculation_id}</strong></td>
                <td>{savedDate(item.created_at)}</td><td>{areaLabel(item.input_data.subject_area)}</td>
                <td><ul className={styles.methods}>{item.saved_results.map((r) => <li key={r.method_name}>{savedMethodName(item, r.method_name)}</li>)}</ul></td>
                <td className={styles.numeric}>{item.median_pmi ?? 'Not calculated'}</td>
                <td><div className={styles.rowActions}>
                  <button className={`${styles.button} ${styles.secondary}`} disabled={deletingId !== null} onClick={() => setSelected(item)} aria-label={`View details for case ${item.calculation_id}`}>View details</button>
                  <button type="button" className={`${styles.button} ${styles.danger} ${styles.iconButton}`}
                    disabled={deletingId !== null} aria-label={`Delete case ${item.calculation_id}`} title={`Delete case #${item.calculation_id}`}
                    aria-busy={deletingId === item.calculation_id} onClick={() => void removeCase(item)}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6" />
                    </svg>
                  </button>
                </div></td>
              </tr>)}</tbody>
            </table>
          </div>
          <div className={styles.pagination}>
            <p role="status">{response.offset + 1}–{response.offset + response.calculations.length} of {response.total} cases</p>
            <div className={styles.filterActions}>
              <button className={`${styles.button} ${styles.secondary}`} disabled={response.offset === 0} onClick={() => setQuery((previous) => ({ ...previous, offset: Math.max(0, previous.offset - response.limit) }))}>Previous</button>
              <button className={`${styles.button} ${styles.secondary}`} disabled={response.offset + response.limit >= response.total} onClick={() => setQuery((previous) => ({ ...previous, offset: previous.offset + response.limit }))}>Next</button>
            </div>
          </div>
        </>
      )}
    </section>
  )
}
