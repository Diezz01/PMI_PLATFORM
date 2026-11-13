import { useRef, useState } from 'react'
import { deleteDraft } from '../services/pmi_chat'

import {
  AssistantRuntimeProvider,
  ComposerPrimitive,
  MessagePrimitive,
  ThreadPrimitive,
  useExternalStoreRuntime,
} from '@assistant-ui/react'

import type {
  AppendMessage,
  ThreadMessageLike,
} from '@assistant-ui/react'

import { usePmiChat } from '../hooks/usePmiChat'
import styles from '../css/PmiChat.module.css'

type Props = {
  draftId: string
  onDeleted: () => void
}

function UserMessage() {
  return (
    <MessagePrimitive.Root className={styles.userMessage}>
      <span className={styles.speaker}>You</span>
      <MessagePrimitive.Parts />
    </MessagePrimitive.Root>
  )
}

function AssistantMessage() {
  return (
    <MessagePrimitive.Root className={styles.assistantMessage}>
      <span className={styles.speaker}>Assistant</span>
      <MessagePrimitive.Parts />
    </MessagePrimitive.Root>
  )
}

export default function PmiChat({ draftId, onDeleted }: Props) {
  const chat = usePmiChat(draftId)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const deletingRef = useRef(false)

  async function removeChat() {
    if (deletingRef.current || chat.working || chat.processing) return
    if (!window.confirm('Delete this conversation and its draft? This cannot be undone.')) return
    deletingRef.current = true
    setDeleting(true)
    setDeleteError('')
    try {
      await deleteDraft(draftId)
    } catch (cause) {
      setDeleteError(cause instanceof Error ? cause.message : 'Unable to delete the conversation.')
      deletingRef.current = false
      setDeleting(false)
      return
    }
    onDeleted()
  }

  const messages: ThreadMessageLike[] = []

  for (const turn of chat.snapshot?.turns ?? []) {
    messages.push({
      id: `${turn.request_id}:user`,
      role: 'user',
      content: [{ type: 'text', text: turn.user_message }],
      createdAt: new Date(turn.created_at),
    })

    if (
      turn.status === 'completed' &&
      turn.assistant_message !== null
    ) {
      messages.push({
        id: `${turn.request_id}:assistant`,
        role: 'assistant',
        content: [{ type: 'text', text: turn.assistant_message }],
      })
    }
  }

  if (
    chat.pending &&
    !chat.snapshot?.turns.some(
      (turn) => turn.request_id === chat.pending?.request_id,
    )
  ) {
    messages.push({
      id: `${chat.pending.request_id}:user`,
      role: 'user',
      content: [{ type: 'text', text: chat.pending.message }],
    })
  }

  async function onNew(message: AppendMessage) {
    if (deletingRef.current) return
    const text = message.content
      .filter((part) => part.type === 'text')
      .map((part) => part.text)
      .join('\n')

    await chat.send(text)
  }

  const runtime = useExternalStoreRuntime({
    messages,
    convertMessage: (message: ThreadMessageLike) => message,
    isRunning: chat.working || chat.processing,
    onNew,
   })

  const draft = chat.snapshot?.draft

  const fields = [
    ['Rectal temperature', draft?.data.rectal_temperature_c, '°C'],
    ['Ambient temperature', draft?.data.ambient_temperature_c, '°C'],
    ['Body weight', draft?.data.body_mass_kg, 'kg'],
    ['Correction factor', draft?.data.correction_factor, ''],
  ] as const

  return (
    <div className={styles.layout}>
      <section className={styles.chatPanel} aria-label="PMI conversation">
        <div className={styles.toolbar}>
          <h1>PMI assistant</h1>
          {/*<button
            type="button"
            onClick={() => void chat.reload()}
            disabled={chat.working || deleting}
          >
            Refresh
          </button>*/}
          <button
            type="button"
            onClick={() => void removeChat()}
            disabled={deleting || chat.working || chat.processing}
          >
            {deleting ? 'Deleting...' : 'Delete chat'}
          </button>
        </div>

        {deleteError && <p className={styles.error} role="alert">{deleteError}</p>}

        {!chat.snapshot && !chat.error && (
          <p role="status">Loading conversation...</p>
        )}

        {chat.error && (
          <div className={styles.error} role="alert">
            <p>{chat.error}</p>
            {chat.pending && (
              <button
                type="button"
                disabled={chat.working || deleting}
                onClick={() => void chat.retryPending()}
              >
                Retry the same request
              </button>
            )}
          </div>
        )}

        {chat.snapshot?.turns
          .filter((turn) => turn.status === 'failed')
          .map((turn) => (
            <p
              className={styles.error}
              role="alert"
              key={turn.request_id}
            >
              Message “{turn.user_message.slice(0, 80)}” failed:
              {' '}{turn.error ?? 'Please review the case data.'}
            </p>
          ))}

        <AssistantRuntimeProvider runtime={runtime}>
          <ThreadPrimitive.Root className={styles.thread}>
            <ThreadPrimitive.Viewport className={styles.viewport}>
              {messages.length === 0 && chat.snapshot && (
                <p className={styles.hint}>
                  Enter your available case data in Italian or English.
                  You can provide several values in one message.
                </p>
              )}

              <ThreadPrimitive.Messages>
                {({ message }) =>
                  message.role === 'user'
                    ? <UserMessage />
                    : <AssistantMessage />
                }
              </ThreadPrimitive.Messages>
            </ThreadPrimitive.Viewport>

            {(chat.working || chat.processing) && (
              <p className={styles.hint} role="status">
                Processing…
                {chat.processing && !chat.working
                  ? ' Use Refresh to check the result.'
                  : ''}
              </p>
            )}

            <ComposerPrimitive.Root className={styles.composer}>
              <ComposerPrimitive.Input
                aria-label="Message"
                placeholder="Enter the available measurements..."
                rows={3}
                maxLength={2000}
                disabled={!chat.canSend || deleting}
              />
              <ComposerPrimitive.Send disabled={!chat.canSend || deleting}>
                Send
              </ComposerPrimitive.Send>
            </ComposerPrimitive.Root>
          </ThreadPrimitive.Root>
        </AssistantRuntimeProvider>
      </section>

      <aside className={styles.summary} aria-label="Case summary">
        <h2>Case summary</h2>
        <p>Values currently stored by the backend.</p>

        <dl>
          {fields.map(([label, value, unit]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>
                {value == null ? 'Not provided' : `${value} ${unit}`.trim()}
              </dd>
            </div>
          ))}
        </dl>

        {draft && (
          <p role="status">
            {draft.status === 'confirmed'
              ? 'Case data confirmed.'
              : draft.can_confirm
                ? 'Required values are complete. Confirmation is still needed.'
                : `${draft.missing_required_fields.length} required field(s) missing.`}
          </p>
        )}

        <p className={styles.hint}>
          This panel shows the four required parameters. Review the complete
          summary in the chat, then confirm there to calculate PMI.
        </p>
      </aside>
    </div>
  )
}
