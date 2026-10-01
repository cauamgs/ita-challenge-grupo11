import type { RecommendationItem } from '../../api/types'
import { formatBRL, formatPct } from '../../lib/format'
import { CHANNEL_LABEL } from '../../lib/labels'
import { ApprovalIcon } from '../Icons'
import { EmptyState, SkeletonRows } from '../States'
import { SortableTh, TableContainer, Td, Th } from '../Table'
import { RecommendationTag, RiskTag, StatusTag } from '../Tag'

const COLUMNS = 13
const DECIDED = new Set(['APROVADA', 'EDITADA', 'REJEITADA'])

export function RecommendationsTable({
  items,
  isLoading,
  sort,
  order,
  onSort,
  onOpen,
  selectedId,
  emptyMessage,
}: {
  items: RecommendationItem[]
  isLoading: boolean
  sort: string
  order: 'asc' | 'desc'
  onSort: (column: string) => void
  onOpen: (id: string) => void
  selectedId: string | null
  emptyMessage: string
}) {
  const sortProps = { sort, order, onSort }
  return (
    <TableContainer maxHeight="calc(100vh - 290px)">
      <thead>
        <tr>
          <SortableTh label="#" column="priority" {...sortProps} numeric />
          <Th>SKU · Produto</Th>
          <Th>Canal</Th>
          <Th numeric>Preço atual</Th>
          <Th numeric>Preço de mercado</Th>
          <Th>Recomendação</Th>
          <Th numeric>Preço sugerido</Th>
          <SortableTh label="Variação" column="variation" {...sortProps} numeric />
          <Th numeric>Margem resultante</Th>
          <SortableTh label="Risco" column="risk" {...sortProps} />
          <SortableTh label="Valor em jogo" column="value_at_stake" {...sortProps} numeric />
          <Th className="text-center">Aprovação</Th>
          <Th>Decisão</Th>
        </tr>
      </thead>
      <tbody>
        {isLoading && <SkeletonRows cols={COLUMNS} />}
        {!isLoading && items.length === 0 && (
          <tr>
            <td colSpan={COLUMNS}>
              <EmptyState title="Nenhuma recomendação encontrada">{emptyMessage}</EmptyState>
            </td>
          </tr>
        )}
        {!isLoading &&
          items.map((item, index) => {
            const decided = DECIDED.has(item.status)
            const selected = item.id === selectedId
            const bg = selected
              ? 'bg-brand-purpleLight'
              : decided
                ? 'bg-decided'
                : index % 2
                  ? 'bg-zebra'
                  : 'bg-surface'
            return (
              <tr
                key={item.id}
                tabIndex={0}
                onClick={() => onOpen(item.id)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    onOpen(item.id)
                  }
                }}
                aria-label={`Abrir detalhe de ${item.sku} ${item.product_name} ${CHANNEL_LABEL[item.channel]}`}
                className={`cursor-pointer border-b border-line ${bg} hover:bg-brand-purpleLight focus-visible:outline-offset-[-2px]`}
              >
                <Td numeric className="text-ink-muted">
                  {item.priority}
                </Td>
                <Td>
                  <span className="font-semibold">{item.sku}</span>
                  <span className="text-ink-muted"> · </span>
                  <span>{item.product_name}</span>
                </Td>
                <Td className="whitespace-nowrap">{CHANNEL_LABEL[item.channel]}</Td>
                <Td numeric>{formatBRL(item.current_price)}</Td>
                <Td numeric>{formatBRL(item.market_price)}</Td>
                <Td>
                  <RecommendationTag value={item.recommendation} />
                </Td>
                <Td numeric>{formatBRL(item.suggested_price)}</Td>
                <Td numeric>{formatPct(item.variation, { sign: true })}</Td>
                <Td numeric>{formatPct(item.resulting_margin)}</Td>
                <Td>
                  <RiskTag value={item.risk_level} />
                </Td>
                <Td numeric>
                  {item.value_at_stake === null ? '—' : `${formatBRL(item.value_at_stake)}/mês`}
                </Td>
                <Td className="text-center">
                  {item.requires_approval ? (
                    <span title="Exige aprovação de gestor" className="inline-flex">
                      <ApprovalIcon />
                      <span className="sr-only">Exige aprovação de gestor</span>
                    </span>
                  ) : null}
                </Td>
                <Td>
                  <StatusTag value={item.status} />
                </Td>
              </tr>
            )
          })}
      </tbody>
    </TableContainer>
  )
}
