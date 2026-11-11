export type DraftStatus = 'collecting' | 'ready' | 'confirmed'

export type DraftData = {
  rectal_temperature_c: number | null
  ambient_temperature_c: number | null
  body_mass_kg: number | null
  correction_factor: number | null

  // Additional case fields remain available without assuming their shape.
  [field: string]: unknown
}

export type PmiDraft = {
  draft_id: string
  data: DraftData
  version: number
  status: DraftStatus
  missing_required_fields: string[]
  can_confirm: boolean
  expires_at: string
}

export type ChatTurn = {
  request_id: string
  user_message: string
  assistant_message: string | null
  status: 'processing' | 'completed' | 'failed'
  created_at: string
  error: string | null
}

export type ChatResponse = {
  draft: PmiDraft
  turns: ChatTurn[]
}

export type ChatRequest = {
  request_id: string
  message: string
}

export type MethodResult = {
  method_id: string
  method_name: string
  method_version: string
  method_kind: 'henssge' | 'biochemical' | 'mock'
  calculation_status:
    | 'calculated'
    | 'missing_input'
    | 'invalid_input'
    | 'invalid_domain'
    | 'blocked'
    | 'error'
  pmi_hours: number | null
  pmi_display: string | null
  time_reference: 'temperature_measurement' | 'sampling' | null
  applicability:
    | 'matched'
    | 'unmatched'
    | 'unverified'
    | 'not_evaluated'
  checks: {
    id: string
    outcome: 'passed' | 'failed' | 'unknown' | 'skipped'
    field: string | null
    message: string
  }[]
}

export type CalculationResponse = {
  session_id: string
  status: 'calculated'
  version: number
  expires_at: string
  source_draft: Record<string, unknown> | null
  evaluated_results: MethodResult[]
  results: {
    method_name: string
    pmi_value: string
    input_params: Record<string, unknown>
    method_version: string
  }[]
}

export class PmiApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'PmiApiError'
    this.status = status
  }
}

const DEFAULT_TIMEOUT_MS = 20_000
const CHAT_TIMEOUT_MS = 330_000

type RequestOptions = {
  method?: 'GET' | 'POST'
  body?: unknown
  timeoutMs?: number
  signal?: AbortSignal
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function errorMessage(status: number, payload: unknown): string {
  if (status === 401) {
    return 'Your session has expired. Please sign in again.'
  }

  if (status === 403) {
    return 'This request is not allowed.'
  }

  if (status === 404) {
    return 'The draft was not found or has expired.'
  }

  if (isRecord(payload)) {
    if (typeof payload.detail === 'string') {
      return payload.detail
    }

    if (Array.isArray(payload.detail)) {
      const messages = payload.detail
        .filter(isRecord)
        .map((issue) => issue.msg)
        .filter((message): message is string => typeof message === 'string')

      if (messages.length > 0) {
        return messages.join(' ')
      }
    }
  }

  return `The request failed (HTTP ${status}).`
}

async function requestJson<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const method = options.method ?? 'GET'
  const timeoutSignal = AbortSignal.timeout(
    options.timeoutMs ?? DEFAULT_TIMEOUT_MS,
  )

  const signal = options.signal
    ? AbortSignal.any([options.signal, timeoutSignal])
    : timeoutSignal

  const headers: Record<string, string> = {}

  if (method !== 'GET') {
    headers['X-PMI-Request'] = '1'
  }

  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json'
  }

  try {
    const response = await fetch(`/api/pmi${path}`, {
      method,
      credentials: 'same-origin',
      cache: 'no-store',
      headers,
      signal,
      body:
        options.body === undefined
          ? undefined
          : JSON.stringify(options.body),
    })

    const text = await response.text()
    let payload: unknown = null

    if (text) {
      try {
        payload = JSON.parse(text)
      } catch {
        if (response.ok) {
          throw new PmiApiError(
            'The server returned an invalid JSON response.',
            response.status,
          )
        }
      }
    }

    if (!response.ok) {
      throw new PmiApiError(
        errorMessage(response.status, payload),
        response.status,
      )
    }

    if (!isRecord(payload)) {
      throw new PmiApiError(
        'The server returned an unexpected response.',
        response.status,
      )
    }

    // TypeScript contract; this is not full runtime schema validation.
    return payload as T
  } catch (error) {
    if (error instanceof PmiApiError) {
      throw error
    }

    if (options.signal?.aborted) {
      throw new PmiApiError(
        'The request was interrupted. The server may still be processing it.',
        0,
      )
    }

    if (timeoutSignal.aborted) {
      throw new PmiApiError(
        'The request timed out. Reload the conversation before retrying.',
        0,
      )
    }

    throw new PmiApiError(
      'Unable to confirm the operation. Check your connection and reload.',
      0,
    )
  }
}

function draftPath(draftId: string): string {
  return `/drafts/${encodeURIComponent(draftId)}`
}

export function createDraft(): Promise<PmiDraft> {
  return requestJson<PmiDraft>('/drafts', {
    method: 'POST',
  })
}

export function getDraft(
  draftId: string,
  signal?: AbortSignal,
): Promise<PmiDraft> {
  return requestJson<PmiDraft>(draftPath(draftId), { signal })
}

export function getChat(
  draftId: string,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  return requestJson<ChatResponse>(
    `${draftPath(draftId)}/chat`,
    { signal },
  )
}

export function sendChatMessage(
  draftId: string,
  request: ChatRequest,
  signal?: AbortSignal,
): Promise<ChatResponse> {
  return requestJson<ChatResponse>(
    `${draftPath(draftId)}/chat`,
    {
      method: 'POST',
      body: request,
      timeoutMs: CHAT_TIMEOUT_MS,
      signal,
    },
  )
}

export function confirmDraft(
  draftId: string,
  expectedVersion: number,
): Promise<PmiDraft> {
  return requestJson<PmiDraft>(
    `${draftPath(draftId)}/confirm`,
    {
      method: 'POST',
      body: { expected_version: expectedVersion },
    },
  )
}

export function calculateDraft(
  draftId: string,
  expectedVersion: number,
): Promise<CalculationResponse> {
  return requestJson<CalculationResponse>(
    `${draftPath(draftId)}/calculate`,
    {
      method: 'POST',
      body: { expected_version: expectedVersion },
    },
  )
}