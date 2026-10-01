import type { ReactNode, ThHTMLAttributes } from 'react'
import { SortIcon } from './Icons'

export function TableContainer({
  children,
  maxHeight,
}: {
  children: ReactNode
  maxHeight?: string
}) {
  return (
    <div
      className="relative overflow-auto rounded-card border border-line"
      style={maxHeight ? { maxHeight } : undefined}
    >
      <table className="w-full min-w-[1100px] border-collapse text-[13px]">{children}</table>
    </div>
  )
}

export function Th({
  children,
  numeric,
  className = '',
  ...props
}: ThHTMLAttributes<HTMLTableCellElement> & { numeric?: boolean }) {
  return (
    <th
      scope="col"
      className={`sticky top-0 z-10 whitespace-nowrap bg-brand-purple px-2 py-2 text-xs font-semibold text-white ${
        numeric ? 'text-right' : 'text-left'
      } ${className}`}
      {...props}
    >
      {children}
    </th>
  )
}

export function SortableTh({
  label,
  column,
  sort,
  order,
  onSort,
  numeric,
}: {
  label: string
  column: string
  sort: string
  order: 'asc' | 'desc'
  onSort: (column: string) => void
  numeric?: boolean
}) {
  const active = sort === column
  return (
    <Th
      numeric={numeric}
      aria-sort={active ? (order === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <button
        type="button"
        onClick={() => onSort(column)}
        className="inline-flex items-center font-semibold hover:underline"
        title={`Ordenar por ${label.toLowerCase()}`}
      >
        {label}
        <SortIcon direction={active ? order : null} />
      </button>
    </Th>
  )
}

export function Td({
  children,
  numeric,
  className = '',
}: {
  children: ReactNode
  numeric?: boolean
  className?: string
}) {
  return (
    <td className={`px-2 py-2 align-middle ${numeric ? 'tabular text-right' : ''} ${className}`}>
      {children}
    </td>
  )
}
