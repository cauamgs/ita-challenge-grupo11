import { useEffect, useRef, type ReactNode } from 'react'
import { CloseIcon } from './Icons'

export function Drawer({
  open,
  onClose,
  title,
  children,
}: {
  open: boolean
  onClose: () => void
  title: string
  children: ReactNode
}) {
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    panelRef.current?.focus()
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-40">
      <div className="absolute inset-0 bg-black/20" onClick={onClose} aria-hidden />
      <aside
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="absolute right-0 top-0 flex h-full w-full max-w-[520px] flex-col bg-surface shadow-[-8px_0_24px_rgba(63,36,96,0.12)] outline-none"
      >
        <button
          onClick={onClose}
          aria-label="Fechar detalhe"
          className="absolute right-3 top-3 z-10 rounded p-1.5 text-ink-muted hover:bg-brand-purpleLight hover:text-brand-purple"
        >
          <CloseIcon />
        </button>
        <div className="flex-1 overflow-y-auto">{children}</div>
      </aside>
    </div>
  )
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return (
    <h3 className="mb-2 text-[10px] font-bold uppercase tracking-[1.5px] text-brand-limeText">
      {children}
    </h3>
  )
}
