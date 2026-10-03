import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

/** Bloco de conteúdo com título de seção (padrão das telas novas). */
export function Card({
  title,
  subtitle,
  action,
  children,
  className = '',
}: {
  title?: string
  subtitle?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <section className={`rounded-card border border-line bg-surface p-4 ${className}`}>
      {(title || action) && (
        <div className="mb-3 flex items-start justify-between gap-3">
          <div>
            {title && <h2 className="text-[15px] font-bold text-brand-purple">{title}</h2>}
            {subtitle && <p className="text-xs text-ink-muted">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </section>
  )
}

export function PageHeader({
  kicker,
  title,
  description,
  actions,
}: {
  kicker?: string
  title: string
  description?: ReactNode
  actions?: ReactNode
}) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-3">
      <div>
        {kicker && (
          <p className="text-[10px] font-bold uppercase tracking-[1.5px] text-brand-limeText">
            {kicker}
          </p>
        )}
        <h2 className="text-[22px] font-bold leading-tight text-brand-purple">{title}</h2>
        {description && <p className="mt-0.5 text-[13px] text-ink-muted">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  )
}

/** Atalho do dashboard: número em destaque + rótulo, leva direto para a análise. */
export function QuickAction({
  to,
  count,
  label,
  hint,
  tone = 'purple',
}: {
  to: string
  count?: number | string
  label: string
  hint: string
  tone?: 'purple' | 'lime' | 'alert'
}) {
  const border = {
    purple: 'border-l-brand-purple',
    lime: 'border-l-brand-lime',
    alert: 'border-l-[#E07A74]',
  }[tone]
  return (
    <Link
      to={to}
      className={`group flex items-center gap-3 rounded-card border border-line border-l-4 ${border} bg-surface px-3 py-2.5 transition hover:border-brand-purpleLine hover:bg-brand-purpleLight`}
    >
      {count !== undefined && (
        <span className="tabular min-w-[2.2rem] text-[22px] font-extrabold leading-none text-brand-purple">
          {count}
        </span>
      )}
      <span className="flex-1">
        <span className="block text-[13px] font-bold text-ink">{label}</span>
        <span className="block text-[11px] text-ink-muted">{hint}</span>
      </span>
      <span aria-hidden className="text-brand-purple transition group-hover:translate-x-0.5">
        →
      </span>
    </Link>
  )
}

export function Breadcrumb({ items }: { items: { label: string; to?: string }[] }) {
  return (
    <nav aria-label="Caminho" className="text-xs text-ink-muted">
      {items.map((item, i) => (
        <span key={item.label}>
          {i > 0 && <span className="mx-1.5">/</span>}
          {item.to ? (
            <Link to={item.to} className="font-semibold text-brand-purple hover:underline">
              {item.label}
            </Link>
          ) : (
            <span>{item.label}</span>
          )}
        </span>
      ))}
    </nav>
  )
}
