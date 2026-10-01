import type { ReactNode } from 'react'

export function KpiCard({
  label,
  value,
  target,
  met,
  note,
}: {
  label: string
  value: ReactNode
  target: string
  met: boolean | null
  note?: string | null
}) {
  return (
    <div className="rounded-card border border-line border-t-4 border-t-brand-purple bg-surface p-3">
      <p className="text-xs text-ink-muted">{label}</p>
      <p
        className={`tabular mt-1 text-[26px] font-extrabold leading-tight ${
          met ? 'text-brand-limeText' : 'text-brand-purple'
        }`}
      >
        {value}
      </p>
      <p className="mt-1 text-xs font-bold text-brand-limeText">
        {target}
        {met && <span className="ml-1 font-semibold">· atingida</span>}
      </p>
      {note && <p className="mt-0.5 text-[11px] text-ink-muted">{note}</p>}
    </div>
  )
}
