import { Link } from 'react-router-dom'
import { useDecisionHistory } from '../api/queries'
import { buildQuery } from '../api/client'
import type { Channel, DecisionType, HistoryFilters } from '../api/types'
import { useSession } from '../app/session'
import { buttonClass } from '../components/Button'
import { Select, TextInput } from '../components/Field'
import { Pagination } from '../components/Pagination'
import { EmptyState, ErrorBox, SkeletonRows } from '../components/States'
import { TableContainer, Td, Th } from '../components/Table'
import { RecommendationTag } from '../components/Tag'
import { formatBRL, formatDate, formatDateTime } from '../lib/format'
import { CHANNEL_LABEL, DECISION_LABEL } from '../lib/labels'
import { useUrlState } from '../lib/useUrlState'

const PAGE_SIZE = 25
const COLUMNS = 12

const DECISION_BG: Record<DecisionType, string> = {
  APROVAR: 'bg-tag-subir',
  EDITAR: 'bg-tag-revisar',
  REJEITAR: 'bg-tag-baixar',
  ADIAR: 'bg-tag-manter',
}

export function HistoryPage() {
  const { users } = useSession()
  const url = useUrlState()
  const page = Math.max(1, Number(url.get('pagina')) || 1)
  const filters: HistoryFilters = {
    user_id: url.get('analista') || undefined,
    decision: (url.get('decisao') || undefined) as DecisionType | undefined,
    channel: (url.get('canal') || undefined) as Channel | undefined,
    date_from: url.get('de') || undefined,
    date_to: url.get('ate') || undefined,
  }
  const { data, isLoading, error } = useDecisionHistory({ ...filters, page, page_size: PAGE_SIZE })
  const change = (updates: Record<string, string>) => url.set(updates, { resetPage: true })
  const hasFilters = Object.values(filters).some(Boolean)

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Select
          label="Analista"
          value={url.get('analista')}
          onChange={(e) => change({ analista: e.target.value })}
        >
          <option value="">Analista: todos</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </Select>
        <Select
          label="Decisão"
          value={url.get('decisao')}
          onChange={(e) => change({ decisao: e.target.value })}
        >
          <option value="">Decisão: todas</option>
          <option value="APROVAR">Aprovada</option>
          <option value="EDITAR">Editada</option>
          <option value="REJEITAR">Rejeitada</option>
          <option value="ADIAR">Adiada</option>
        </Select>
        <Select
          label="Canal"
          value={url.get('canal')}
          onChange={(e) => change({ canal: e.target.value })}
        >
          <option value="">Canal: todos</option>
          <option value="LOJA_FISICA">Loja física</option>
          <option value="ECOMMERCE">E-commerce</option>
          <option value="MARKETPLACE">Marketplace</option>
        </Select>
        <span className="text-xs text-ink-muted">Período</span>
        <TextInput
          label="Data inicial"
          type="date"
          value={url.get('de')}
          onChange={(e) => change({ de: e.target.value })}
        />
        <span className="text-xs text-ink-muted">até</span>
        <TextInput
          label="Data final"
          type="date"
          value={url.get('ate')}
          onChange={(e) => change({ ate: e.target.value })}
        />
        <a
          href={`/api/decisions/export${buildQuery({ ...filters })}`}
          download
          className={buttonClass('secondary', 'ml-auto')}
        >
          Exportar CSV
        </a>
      </div>

      {error ? (
        <ErrorBox error={error} />
      ) : (
        <TableContainer maxHeight="calc(100vh - 230px)">
          <thead>
            <tr>
              <Th>Data/hora</Th>
              <Th>Analista</Th>
              <Th>SKU</Th>
              <Th>Produto</Th>
              <Th>Canal</Th>
              <Th>Rodada</Th>
              <Th>Recomendação</Th>
              <Th numeric>Preço sugerido</Th>
              <Th>Decisão</Th>
              <Th numeric>Preço aplicado</Th>
              <Th>Motivo</Th>
              <Th>Comentário</Th>
            </tr>
          </thead>
          <tbody>
            {isLoading && <SkeletonRows cols={COLUMNS} />}
            {!isLoading && data?.items.length === 0 && (
              <tr>
                <td colSpan={COLUMNS}>
                  <EmptyState
                    title={hasFilters ? 'Nenhuma decisão encontrada' : 'Nenhuma decisão registrada'}
                  >
                    {hasFilters
                      ? 'Ajuste ou limpe os filtros.'
                      : 'As decisões do analista aparecem aqui assim que forem registradas.'}
                  </EmptyState>
                </td>
              </tr>
            )}
            {!isLoading &&
              data?.items.map((d, i) => (
                <tr key={d.id} className={`border-b border-line ${i % 2 ? 'bg-zebra' : ''}`}>
                  <Td className="tabular whitespace-nowrap">{formatDateTime(d.created_at)}</Td>
                  <Td className="whitespace-nowrap">
                    <Link
                      to={`/analistas/${d.user_id}`}
                      className="hover:text-brand-purple hover:underline"
                    >
                      {d.user_name}
                    </Link>
                  </Td>
                  <Td>
                    <Link
                      to={`/produtos/${d.sku}`}
                      className="font-semibold text-brand-purple hover:underline"
                    >
                      {d.sku}
                    </Link>
                  </Td>
                  <Td>{d.product_name}</Td>
                  <Td className="whitespace-nowrap">{CHANNEL_LABEL[d.channel]}</Td>
                  <Td className="tabular">{formatDate(d.round_date)}</Td>
                  <Td>
                    <RecommendationTag value={d.snapshot_recommendation} />
                  </Td>
                  <Td numeric>{formatBRL(d.snapshot_suggested_price)}</Td>
                  <Td>
                    <span
                      className={`inline-flex h-5 items-center rounded-[10px] px-2 text-[11px] font-bold ${DECISION_BG[d.decision]}`}
                    >
                      {DECISION_LABEL[d.decision]}
                    </span>
                  </Td>
                  <Td numeric>{formatBRL(d.applied_price)}</Td>
                  <Td>{d.rejection_reason ?? '—'}</Td>
                  <Td className="max-w-[240px] truncate">
                    <span title={d.comment ?? undefined}>{d.comment ?? '—'}</span>
                  </Td>
                </tr>
              ))}
          </tbody>
        </TableContainer>
      )}
      <Pagination
        page={page}
        pageSize={PAGE_SIZE}
        total={data?.total ?? 0}
        onChange={(p) => url.set({ pagina: p === 1 ? null : String(p) })}
      />
    </div>
  )
}
