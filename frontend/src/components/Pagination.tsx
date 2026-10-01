import { Button } from './Button'

export function Pagination({
  page,
  pageSize,
  total,
  onChange,
}: {
  page: number
  pageSize: number
  total: number
  onChange: (page: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  if (total === 0) return null
  const from = (page - 1) * pageSize + 1
  const to = Math.min(total, page * pageSize)
  return (
    <div className="flex items-center justify-between gap-2 py-3 text-xs text-ink-muted">
      <span className="tabular">
        {from}–{to} de {total} itens
      </span>
      <div className="flex items-center gap-2">
        <Button variant="ghost" disabled={page <= 1} onClick={() => onChange(page - 1)}>
          Anterior
        </Button>
        <span className="tabular">
          Página {page} de {pages}
        </span>
        <Button variant="ghost" disabled={page >= pages} onClick={() => onChange(page + 1)}>
          Próxima
        </Button>
      </div>
    </div>
  )
}
