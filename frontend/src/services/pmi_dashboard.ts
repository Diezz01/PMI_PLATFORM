import { requestJson } from './pmi_chat'
import type { MethodResult } from './pmi_chat'

export type CorrectionFactor = {
  id: number
  cf_value: number
  dry_clothing_or_covering: string | null
  in_air: string | null
  wet_through_clothing_or_covering_or_wet_body_surface: string | null
  water: string | null
}

export type SavedCase = {
  calculation_id: number
  input_data: Record<string, unknown>
  median_selected_methods: string[]
  median_pmi: string | null
  created_at: string
  saved_results: {
    method_name: string
    pmi_value: string
    method_version: string
    input_params: Record<string, unknown>
  }[]
  evaluation_snapshot: {
    evaluated_results?: Omit<MethodResult, 'pmi_display' | 'applicability'>[]
    result_selection?: { acknowledged_warning_method_ids?: string[] }
    median_result?: { acknowledged_warning_method_ids?: string[] }
  } | null
}

export type HistoryResponse = {
  calculations: SavedCase[]
  total: number
  limit: number
  offset: number
}

export type HistoryMethod = { method_id: string; label: string }
export type HistoryFilters = {
  caseId: string
  dateFrom: string
  dateTo: string
  method: string
  subjectArea: string
  median: '' | 'true' | 'false'
  sort: 'newest' | 'oldest'
}

export const emptyHistoryFilters: HistoryFilters = {
  caseId: '', dateFrom: '', dateTo: '', method: '', subjectArea: '', median: '', sort: 'newest',
}

export function getCorrectionFactors(signal?: AbortSignal) {
  return requestJson<{ correction_factors: CorrectionFactor[] }>('/correction-factors', { signal })
}

export function getHistoryMethods(signal?: AbortSignal) {
  return requestJson<{ methods: HistoryMethod[] }>('/history/methods', { signal })
}

export function deleteSavedCase(calculationId: number): Promise<void> {
  return requestJson<void>(`/history/${calculationId}`, { method: 'DELETE' })
}

function dateBoundary(value: string, nextDay = false): string {
  const date = new Date(`${value}T00:00:00`)
  if (nextDay) date.setDate(date.getDate() + 1)
  return date.toISOString()
}

export function getHistory(filters: HistoryFilters, offset: number, signal?: AbortSignal) {
  const query = new URLSearchParams({ limit: '10', offset: String(offset), sort: filters.sort })
  if (filters.caseId) query.set('case_id', filters.caseId)
  if (filters.dateFrom) query.set('saved_from', dateBoundary(filters.dateFrom))
  if (filters.dateTo) query.set('saved_before', dateBoundary(filters.dateTo, true))
  if (filters.method) query.set('method', filters.method)
  if (filters.subjectArea) query.set('subject_area', filters.subjectArea)
  if (filters.median) query.set('has_median', filters.median)
  return requestJson<HistoryResponse>(`/history?${query}`, { signal })
}
