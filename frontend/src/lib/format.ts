const brl = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })
const pct1 = new Intl.NumberFormat('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
const num1 = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 1 })
const int = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 0 })

export const EMPTY = '—'
const NBSP = new RegExp(String.fromCharCode(160), 'g')

/** formatBRL(1234.5) → "R$ 1.234,50" */
export function formatBRL(value: number | null | undefined): string {
  if (value === null || value === undefined) return EMPTY
  return brl.format(value).replace(NBSP, ' ')
}

/** formatPct(0.023, { sign: true }) → "+2,3%" (valor em fração) */
export function formatPct(value: number | null | undefined, opts: { sign?: boolean } = {}): string {
  if (value === null || value === undefined) return EMPTY
  const pct = value * 100
  const rounded = Math.round(pct * 10) / 10
  const sign = opts.sign && rounded > 0 ? '+' : ''
  return `${sign}${pct1.format(rounded === 0 ? 0 : rounded)}%`
}

export function formatNumber(value: number | null | undefined, digits: 0 | 1 = 1): string {
  if (value === null || value === undefined) return EMPTY
  return digits === 0 ? int.format(value) : num1.format(value)
}

/** formatDate("2026-09-09") → "09/09/2026" */
export function formatDate(value: string | null | undefined): string {
  if (!value) return EMPTY
  const [y, m, d] = value.slice(0, 10).split('-')
  return `${d}/${m}/${y}`
}

/** formatDateTime(ISO) → "09/09/2026 14:32" no fuso local */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return EMPTY
  const date = new Date(value)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${p(date.getDate())}/${p(date.getMonth() + 1)}/${date.getFullYear()} ${p(date.getHours())}:${p(date.getMinutes())}`
}

/** Lê um preço digitado em pt-BR ("1.234,56", "214,9") ou com ponto decimal ("214.90"). */
export function parsePrice(text: string): number | null {
  const clean = text.replace(/R\$|\s/g, '')
  if (!clean) return null
  const normalized = clean.includes(',') ? clean.replace(/\./g, '').replace(',', '.') : clean
  const value = Number(normalized)
  return Number.isFinite(value) ? value : null
}

/** "há 5 min", "há 3 h", "há 2 dias"; datas futuras: "em 3 h", "em 2 dias". */
export function formatRelative(value: string | null | undefined, now: Date = new Date()): string {
  if (!value) return EMPTY
  const diff = new Date(value).getTime() - now.getTime()
  const future = diff > 0
  const minutes = Math.round(Math.abs(diff) / 60_000)
  let text: string
  if (minutes < 1) return future ? 'em instantes' : 'agora há pouco'
  if (minutes < 60) text = `${minutes} min`
  else if (minutes < 60 * 24) text = `${Math.round(minutes / 60)} h`
  else {
    const days = Math.round(minutes / (60 * 24))
    text = `${days} ${days === 1 ? 'dia' : 'dias'}`
  }
  return future ? `em ${text}` : `há ${text}`
}

const WEEKDAY_SHORT = ['dom.', 'seg.', 'ter.', 'qua.', 'qui.', 'sex.', 'sáb.']

/** "sáb., 10/10/2026 às 06:00" */
export function formatWeekdayDateTime(value: string | null | undefined): string {
  if (!value) return EMPTY
  const date = new Date(value)
  const [day, time] = formatDateTime(value).split(' ')
  return `${WEEKDAY_SHORT[date.getDay()]}, ${day} às ${time}`
}

const MONTHS = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

/** "2026-09" → "set/26" */
export function formatMonth(value: string): string {
  const [y, m] = value.split('-')
  return `${MONTHS[Number(m) - 1]}/${y.slice(2)}`
}

/** "2026-09-30" → "30/09" */
export function formatDayMonth(value: string): string {
  const [, m, d] = value.slice(0, 10).split('-')
  return `${d}/${m}`
}

/** plural(1, 'redução', 'reduções') → "1 redução" */
export function plural(n: number, singular: string, pluralForm: string): string {
  return `${n} ${n === 1 ? singular : pluralForm}`
}
