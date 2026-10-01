import type { ReactNode } from 'react'

export function Loading({ label = 'Carregando…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-2 py-8 text-ink-muted">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-purpleLine border-t-brand-purple" />
      {label}
    </div>
  )
}

export function SkeletonRows({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, r) => (
        <tr key={r} aria-hidden>
          {Array.from({ length: cols }).map((__, c) => (
            <td key={c} className="px-2 py-2.5">
              <div className="h-3 animate-pulse rounded bg-brand-purpleLight" />
            </td>
          ))}
        </tr>
      ))}
    </>
  )
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-1 py-10 text-center">
      <p className="text-[15px] font-bold text-brand-purple">{title}</p>
      {children && <p className="text-xs text-ink-muted">{children}</p>}
    </div>
  )
}

export function ErrorBox({ error }: { error: unknown }) {
  const message = error instanceof Error ? error.message : 'Erro inesperado.'
  return (
    <div
      role="alert"
      className="rounded-card border-l-4 border-[#E07A74] bg-tag-baixar px-3 py-2 text-ink"
    >
      {message}
    </div>
  )
}

export function Callout({
  tone = 'lime',
  children,
}: {
  tone?: 'lime' | 'purple'
  children: ReactNode
}) {
  const cls =
    tone === 'lime'
      ? 'border-brand-lime bg-brand-limeLight'
      : 'border-brand-purple bg-brand-purpleLight'
  return <div className={`rounded-card border-l-4 px-3 py-2 ${cls}`}>{children}</div>
}
