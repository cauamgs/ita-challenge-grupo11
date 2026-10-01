import { useCallback, useMemo } from 'react'
import { useRecommendations } from '../api/queries'
import type { RecommendationFilters } from '../api/types'
import { useSession } from '../app/session'
import { buttonClass } from '../components/Button'
import { Drawer } from '../components/Drawer'
import { Pagination } from '../components/Pagination'
import { DecisionPanel } from '../components/recommendations/DecisionPanel'
import { ImportRoundButton } from '../components/recommendations/ImportRoundButton'
import { ItemHistory } from '../components/recommendations/ItemHistory'
import { RecommendationDetailView } from '../components/recommendations/RecommendationDetail'
import {
  RecommendationFiltersBar,
  type FilterValues,
} from '../components/recommendations/RecommendationFiltersBar'
import { RecommendationsTable } from '../components/recommendations/RecommendationsTable'
import { RoundSummaryBox } from '../components/recommendations/RoundSummaryBox'
import { EmptyState, ErrorBox, Loading } from '../components/States'
import { useUrlState } from '../lib/useUrlState'

const PAGE_SIZE = 25
const FILTER_KEYS: (keyof FilterValues)[] = [
  'canal', 'curva', 'recomendacao', 'risco', 'status', 'aprovacao', 'q',
] // prettier-ignore

export function RecommendationsPage() {
  const { currentRound, isLoading: sessionLoading } = useSession()
  const url = useUrlState()

  const values = useMemo(
    () => Object.fromEntries(FILTER_KEYS.map((k) => [k, url.get(k)])) as unknown as FilterValues,
    [url],
  )
  const sort = (url.get('ordem') || 'priority') as NonNullable<RecommendationFilters['sort']>
  const order = (url.get('dir') || 'asc') as 'asc' | 'desc'
  const page = Math.max(1, Number(url.get('pagina')) || 1)
  const selectedId = url.get('item') || null

  const filters: RecommendationFilters = {
    channel: (values.canal || undefined) as RecommendationFilters['channel'],
    abc_curve: (values.curva || undefined) as RecommendationFilters['abc_curve'],
    recommendation: (values.recomendacao || undefined) as RecommendationFilters['recommendation'],
    risk_level: (values.risco || undefined) as RecommendationFilters['risk_level'],
    status: (values.status || undefined) as RecommendationFilters['status'],
    requires_approval: values.aprovacao === '1' ? true : undefined,
    q: values.q || undefined,
    sort,
    order,
    page,
    page_size: PAGE_SIZE,
  }
  const list = useRecommendations(currentRound?.id, filters)

  const { set } = url
  const onFilterChange = useCallback(
    (updates: Partial<FilterValues>) => set(updates as Record<string, string>, { resetPage: true }),
    [set],
  )
  const onSort = (column: string) => {
    const defaultDesc = column === 'value_at_stake' || column === 'risk'
    const nextOrder =
      sort === column ? (order === 'asc' ? 'desc' : 'asc') : defaultDesc ? 'desc' : 'asc'
    set({
      ordem: column === 'priority' ? null : column,
      dir: nextOrder === 'asc' ? null : nextOrder,
    })
  }
  const closeDrawer = useCallback(() => set({ item: null }), [set])
  const hasFilters = FILTER_KEYS.some((k) => values[k])

  if (sessionLoading) return <Loading />
  if (!currentRound)
    return (
      <div className="flex flex-col items-center">
        <EmptyState title="Nenhuma rodada importada">
          Importe um arquivo de recomendações para começar.
        </EmptyState>
        <ImportRoundButton />
      </div>
    )

  return (
    <div className="space-y-3">
      <RoundSummaryBox roundId={currentRound.id} />
      <RecommendationFiltersBar
        values={values}
        onChange={onFilterChange}
        actions={
          <>
            <ImportRoundButton />
            <a
              href={`/api/rounds/${currentRound.id}/export`}
              download
              className={buttonClass('secondary')}
              title="Baixar CSV com as decisões Aprovar e Editar desta rodada"
            >
              Exportar aprovadas
            </a>
          </>
        }
      />
      {list.error ? (
        <ErrorBox error={list.error} />
      ) : (
        <>
          <RecommendationsTable
            items={list.data?.items ?? []}
            isLoading={list.isLoading}
            sort={sort}
            order={order}
            onSort={onSort}
            onOpen={(id) => set({ item: id })}
            selectedId={selectedId}
            emptyMessage={
              hasFilters
                ? 'Nenhum item corresponde aos filtros. Ajuste ou limpe os filtros.'
                : 'Esta rodada não tem recomendações.'
            }
          />
          <Pagination
            page={page}
            pageSize={PAGE_SIZE}
            total={list.data?.total ?? 0}
            onChange={(p) => set({ pagina: p === 1 ? null : String(p) })}
          />
        </>
      )}
      <Drawer open={!!selectedId} onClose={closeDrawer} title="Detalhe da recomendação">
        {selectedId && (
          <RecommendationDetailView
            id={selectedId}
            decisionSlot={(detail) => (
              <>
                <DecisionPanel key={detail.id} detail={detail} />
                <ItemHistory detail={detail} />
              </>
            )}
          />
        )}
      </Drawer>
    </div>
  )
}
