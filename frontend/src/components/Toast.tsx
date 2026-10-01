import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'

type Tone = 'success' | 'warning' | 'error'
interface ToastItem {
  id: number
  tone: Tone
  title: string
  lines?: string[]
}

const ToastContext = createContext<(t: Omit<ToastItem, 'id'>) => void>(() => {})

const TONE: Record<Tone, string> = {
  success: 'border-brand-lime bg-brand-limeLight',
  warning: 'border-[#E5C04B] bg-tag-revisar',
  error: 'border-[#E07A74] bg-tag-baixar',
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const push = useCallback((t: Omit<ToastItem, 'id'>) => {
    const id = Date.now() + Math.random()
    setItems((prev) => [...prev, { ...t, id }])
    setTimeout(
      () => setItems((prev) => prev.filter((i) => i.id !== id)),
      t.lines?.length ? 7000 : 3500,
    )
  }, [])

  return (
    <ToastContext.Provider value={push}>
      {children}
      <div aria-live="polite" className="fixed bottom-4 left-4 z-[60] flex w-80 flex-col gap-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={`rounded-card border-l-4 px-3 py-2 text-[13px] shadow ${TONE[t.tone]}`}
          >
            <p className="font-bold">{t.title}</p>
            {t.lines?.map((line) => (
              <p key={line} className="text-xs">
                {line}
              </p>
            ))}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useToast() {
  return useContext(ToastContext)
}
