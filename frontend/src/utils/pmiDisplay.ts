import type { SavedCase } from '../services/pmi_dashboard'

export const subjectAreas = [
  ['north_america', 'North America'], ['usa', 'USA'], ['south_america', 'South America'],
  ['europe', 'Europe'], ['north_europe', 'Northern Europe'], ['scandinavia', 'Scandinavia'],
  ['west_europe', 'Western Europe'], ['china', 'China'], ['india', 'India'], ['north_africa', 'North Africa'],
] as const

export function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function readableLabel(value: string): string {
  return value.replaceAll('_', ' ').replace(/^./, (first) => first.toUpperCase())
}

export function areaLabel(value: unknown): string {
  return subjectAreas.find(([id]) => id === value)?.[1]
    ?? (typeof value === 'string' && value ? readableLabel(value) : 'Not provided')
}

export function savedMethodName(item: SavedCase, id: string): string {
  return item.evaluation_snapshot?.evaluated_results?.find((r) => r.method_id === id)?.method_name
    ?? (id === 'henssge' ? 'Henssge' : readableLabel(id))
}

export function savedDate(value: string): string {
  return new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value))
}

export function measurementLabel(value: unknown, fallbackUnit = ''): string {
  if (value == null) return 'Not provided'
  if (isRecord(value)) {
    if (value.status === 'unavailable') return 'Not available'
    const units: Record<string, string> = { mmol_l: 'mmol/L', mg_dl: 'mg/dL', g_l: 'g/L' }
    const unit = typeof value.unit === 'string' ? units[value.unit] ?? value.unit : fallbackUnit
    const result = value.value == null ? 'Not provided'
      : unit ? `${value.value} ${unit}` : `${value.value} (unit not recorded)`
    if (isRecord(value.technique)) {
      const technique = value.technique
      const names: Record<string, string> = {
        photometer: 'Photometry', potentiometer: 'Potentiometry', hplc: 'HPLC', lc_msms: 'LC-MS/MS',
      }
      const label = technique.mode === 'all' ? 'All techniques'
        : technique.mode === 'specific' && typeof technique.id === 'string'
          ? names[technique.id] ?? readableLabel(technique.id) : 'Technique unknown'
      return `${result} · ${label}`
    }
    return result
  }
  return `${value} ${fallbackUnit}`.trim()
}
