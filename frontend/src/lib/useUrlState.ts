import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

/** Estado de filtros guardado na query string (compartilhável). Valores vazios são removidos. */
export function useUrlState() {
  const [params, setParams] = useSearchParams()

  const get = useCallback((key: string) => params.get(key) ?? '', [params])

  const set = useCallback(
    (updates: Record<string, string | null>, opts: { resetPage?: boolean } = {}) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          for (const [key, value] of Object.entries(updates)) {
            if (value === null || value === '') next.delete(key)
            else next.set(key, value)
          }
          if (opts.resetPage) next.delete('pagina')
          return next
        },
        { replace: true },
      )
    },
    [setParams],
  )

  return { params, get, set }
}
