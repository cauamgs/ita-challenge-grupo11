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
