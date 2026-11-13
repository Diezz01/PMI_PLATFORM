import { useCallback, useEffect, useRef, useState } from 'react'

import {
  getChat,
  sendChatMessage,
} from '../services/pmi_chat'

import type {
  ChatRequest,
  ChatResponse,
} from '../services/pmi_chat'

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : 'Unexpected error.'
}

export function usePmiChat(draftId: string) {
  const [snapshot, setSnapshot] = useState<ChatResponse | null>(null)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState('')
  const [pending, setPending] = useState<ChatRequest | null>(null)

  const operationRef = useRef(false)
  const mountedRef = useRef(false)

  useEffect(() => {
    mountedRef.current = true
    const controller = new AbortController()

    void getChat(draftId, controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) {
          setSnapshot(response)
          setError('')
        }
      })
      .catch((cause: unknown) => {
        if (!controller.signal.aborted) {
          setError(describeError(cause))
        }
      })

    return () => {
      mountedRef.current = false
      controller.abort()
    }
  }, [draftId])

  const reload = useCallback(async () => {
    if (operationRef.current) return

    operationRef.current = true
    setWorking(true)

    try {
      const response = await getChat(draftId)

      if (!mountedRef.current) return

      setSnapshot(response)
      setError('')

      // Only discard an uncertain request when the backend knows it.
      if (
        pending &&
        response.turns.some(
          (turn) => turn.request_id === pending.request_id,
        )
      ) {
        setPending(null)
      }
    } catch (cause) {
      if (mountedRef.current) setError(describeError(cause))
    } finally {
      operationRef.current = false
      if (mountedRef.current) setWorking(false)
    }
  }, [draftId, pending])

  const submit = useCallback(async (request: ChatRequest) => {
    if (operationRef.current) return

    operationRef.current = true
    setWorking(true)
    setPending(request)
    setError('')

    try {
      const response = await sendChatMessage(draftId, request)

      if (!mountedRef.current) return

      setSnapshot(response)
      setPending(null)
    } catch (cause) {
      if (mountedRef.current) {
        setError(describeError(cause))
        // Keep the same request ID for an explicit retry.
      }
    } finally {
      operationRef.current = false
      if (mountedRef.current) setWorking(false)
    }
  }, [draftId])

  const processing = snapshot?.turns.some(
    (turn) => turn.status === 'processing',
  ) ?? false

  const canSend = (
    snapshot !== null &&
    !working &&
    !processing &&
    pending === null
  )

  async function send(text: string): Promise<void> {
    const message = text.trim()

    if (!message || !canSend || operationRef.current) return

    if (message.length > 2000) {
      setError('Please use at most 2,000 characters.')
      return
    }

    await submit({
      request_id: crypto.randomUUID(),
      message,
    })
  }

  async function retryPending(): Promise<void> {
    if (pending) await submit(pending)
  }

  return {
    snapshot,
    working,
    processing,
    pending,
    error,
    canSend,
    send,
    reload,
    retryPending,
  }
}