import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from 'react'

export const fieldClass =
  'h-8 rounded border border-brand-purpleLine bg-brand-purpleLight px-2 text-[13px] text-ink'

export function Select({
  label,
  className = '',
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string; children: ReactNode }) {
  return (
    <label className="inline-flex flex-col gap-0.5">
      <span className="sr-only">{label}</span>
      <select aria-label={label} className={`${fieldClass} pr-7 ${className}`} {...props}>
        {children}
      </select>
    </label>
  )
}

export function TextInput({
  label,
  className = '',
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="inline-flex flex-col">
      <span className="sr-only">{label}</span>
      <input aria-label={label} className={`${fieldClass} ${className}`} {...props} />
    </label>
  )
}

export function FieldLabel({ children }: { children: ReactNode }) {
  return <span className="mb-1 block text-xs text-ink-muted">{children}</span>
}
