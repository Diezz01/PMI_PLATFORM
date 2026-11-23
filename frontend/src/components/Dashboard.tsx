import { useCallback, useEffect, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'

import { createDraft } from '../services/pmi_chat'
import PmiChat from './PmiChat'
import CorrectionFactors from './CorrectionFactors'
import SavedCases from './SavedCases'
import styles from '../css/Dashboard.module.css'

type Props = {
  userId: number
}

export default function Dashboard({ userId }: Props) {
  const storageKey = `pmi:active-draft:${userId}`

  const [draftId, setDraftId] = useState<string | null>(() => {
    try {
      return sessionStorage.getItem(storageKey)
    } catch {
      return null
    }
  })

  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')
  const creatingRef = useRef(false)
  const mountedRef = useRef(false)
  const [tab, setTab] = useState(0)
  const [savedRevision, setSavedRevision] = useState(0)
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([])

  const startDraft = useCallback(async () => {
    if (creatingRef.current) return

    creatingRef.current = true
    setCreating(true)
    setError('')

    try {
      const draft = await createDraft()
      if (!mountedRef.current) return

      try {
        sessionStorage.setItem(storageKey, draft.draft_id)
      } catch {
        // The chat remains usable without browser storage.
      }

      setDraftId(draft.draft_id)
    } catch (cause) {
      if (mountedRef.current) setError(
        cause instanceof Error
          ? cause.message
          : 'Unable to create the draft.',
      )
    } finally {
      creatingRef.current = false
      if (mountedRef.current) setCreating(false)
    }
  }, [storageKey])

  useEffect(() => {
    mountedRef.current = true
    return () => { mountedRef.current = false }
  }, [])

  useEffect(() => {
    if (!draftId && !error) void startDraft()
  }, [draftId, error, startDraft])

  const resetDraft = useCallback(() => {
    try { sessionStorage.removeItem(storageKey) } catch { /* Storage is optional. */ }
    setError('')
    setDraftId(null)
  }, [storageKey])

  const onSaved = useCallback(() => setSavedRevision((value) => value + 1), [])

  function moveTab(event: KeyboardEvent<HTMLButtonElement>, index: number) {
    const next = event.key === 'ArrowRight' ? (index + 1) % 3
      : event.key === 'ArrowLeft' ? (index + 2) % 3
        : event.key === 'Home' ? 0 : event.key === 'End' ? 2 : null
    if (next === null) return
    event.preventDefault()
    setTab(next)
    tabRefs.current[next]?.focus()
  }

  return (
    <div className={styles.dashboard}>
      <div className={styles.navigation}>
        <div className={styles.tabs} role="tablist" aria-label="PMI workspace">
          {['PMI assistant', 'Correction factors', 'Saved cases'].map((label, index) => (
            <button key={label} type="button" role="tab" className={styles.tab}
              id={`workspace-tab-${index}`} aria-controls={`workspace-panel-${index}`}
              aria-selected={tab === index} tabIndex={tab === index ? 0 : -1}
              ref={(element) => { tabRefs.current[index] = element }}
              onClick={() => setTab(index)} onKeyDown={(event) => moveTab(event, index)}>{label}</button>
          ))}
        </div>
      </div>
      <div className={styles.content}>
        <div className={styles.panel} id="workspace-panel-0" role="tabpanel" aria-labelledby="workspace-tab-0" hidden={tab !== 0}>
          {draftId ? <PmiChat key={draftId} draftId={draftId} onDeleted={resetDraft} onExpired={resetDraft} onSaved={onSaved} /> : (
            <section className={styles.card} aria-label="Opening conversation">
              <div className={styles.heading}><h1>PMI assistant</h1></div>
              {error ? <div role="alert"><p className={styles.error}>{error}</p>
                <button className={styles.button} disabled={creating} onClick={() => void startDraft()}>Try again</button></div>
                : <p role="status">Opening your conversation...</p>}
            </section>
          )}
        </div>
        <div className={styles.panel} id="workspace-panel-1" role="tabpanel" aria-labelledby="workspace-tab-1" hidden={tab !== 1}>
          <CorrectionFactors active={tab === 1} />
        </div>
        <div className={styles.panel} id="workspace-panel-2" role="tabpanel" aria-labelledby="workspace-tab-2" hidden={tab !== 2}>
          <SavedCases active={tab === 2} revision={savedRevision} />
        </div>
      </div>
    </div>
  )
}
