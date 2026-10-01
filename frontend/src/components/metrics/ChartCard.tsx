import type { ReactNode } from 'react'

export function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string
  subtitle?: string
  children: ReactNode
}) {
  return (
    <section className="rounded-card border border-line bg-surface p-4">
      <h2 className="text-[15px] font-bold text-brand-purple">{title}</h2>
      {subtitle && <p className="text-xs text-ink-muted">{subtitle}</p>}
      <div className="mt-3">{children}</div>
    </section>
  )
}

/** Tooltip no estilo da marca (texto sempre em ink; a cor fica só no marcador). */
export function ChartTooltip({
  active,
  label,
  rows,
}: {
  active?: boolean
  label?: string
  rows: { name: string; value: string; color?: string }[]
}) {
  if (!active || rows.length === 0) return null
  return (
    <div className="rounded-card border border-line bg-surface px-3 py-2 text-xs shadow">
      {label && <p className="mb-1 font-bold text-ink">{label}</p>}
      {rows.map((r) => (
        <p key={r.name} className="flex items-center gap-1.5 text-ink">
          {r.color && (
            <span
              className="inline-block h-2.5 w-2.5 rounded-sm border border-black/20"
              style={{ background: r.color }}
            />
          )}
          <span className="text-ink-muted">{r.name}:</span>
          <span className="tabular font-semibold">{r.value}</span>
        </p>
      ))}
    </div>
  )
}
