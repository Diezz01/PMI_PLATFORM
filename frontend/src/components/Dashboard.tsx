import { useRef, useState } from 'react'

import { createDraft } from '../services/pmi_chat'
import PmiChat from './PmiChat'

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

  async function startDraft() {
    if (creatingRef.current) return

    creatingRef.current = true
    setCreating(true)
    setError('')

    try {
      const draft = await createDraft()

      try {
        sessionStorage.setItem(storageKey, draft.draft_id)
      } catch {
        // The chat remains usable without browser storage.
      }

      setDraftId(draft.draft_id)
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : 'Unable to create the draft.',
      )
    } finally {
      creatingRef.current = false
      setCreating(false)
    }
  }

  if (draftId) {
    return <PmiChat key={draftId} draftId={draftId} onDeleted={() => {
      try {
        sessionStorage.removeItem(storageKey)
      } catch {
        // Closing the current view still works without browser storage.
      }
      setDraftId(null)
    }} />
  }

  return (
    <section>
      <h1>New PMI case</h1>
      <p>Start a conversation to collect the available case data.</p>

      {error && <p role="alert">{error}</p>}

      <button
        type="button"
        disabled={creating}
        onClick={() => void startDraft()}
      >
        {creating ? 'Creating...' : 'Start conversation'}
      </button>
    </section>
  )
}
