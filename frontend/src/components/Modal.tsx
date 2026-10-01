import { useEffect, useRef, type ReactNode } from 'react'
import { CloseIcon } from './Icons'

export function Modal({
  open,
  title,
  onClose,
  children,
  footer,
}: {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
  footer: ReactNode
}) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation()
        onClose()
      }
    }
    // captura para o Esc fechar só o modal, não o drawer atrás
    document.addEventListener('keydown', onKey, true)
    ref.current?.querySelector<HTMLElement>('input, select, textarea, button')?.focus()
    return () => document.removeEventListener('keydown', onKey, true)
  }, [open, onClose])

  if (!open) return null
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} aria-hidden />
      <div
        ref={ref}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="relative w-full max-w-md rounded-card border-t-4 border-brand-purple bg-surface shadow-xl"
      >
        <div className="flex items-center justify-between px-4 pb-2 pt-3">
          <h2 className="text-[15px] font-bold text-brand-purple">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="rounded p-1 text-ink-muted hover:bg-brand-purpleLight"
          >
            <CloseIcon />
          </button>
        </div>
        <div className="space-y-3 px-4 pb-3">{children}</div>
        <div className="flex justify-end gap-2 border-t border-line px-4 py-3">{footer}</div>
      </div>
    </div>
  )
}
