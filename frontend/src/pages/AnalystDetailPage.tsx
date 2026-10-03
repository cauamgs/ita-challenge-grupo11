import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { buildQuery } from '../api/client'
import { useAnalyst } from '../api/platform'
import { useDecisionHistory } from '../api/queries'
import type { DecisionType, RecommendationType } from '../api/types'
import { buttonClass } from '../components/Button'
import { Breadcrumb, Card, PageHeader } from '../components/Card'
import { DecisionsByDayChart } from '../components/charts/PlatformCharts'
import { KpiCard } from '../components/metrics/KpiCard'
import { Pagination } from '../components/Pagination'
import { EmptyState, ErrorBox, Loading, SkeletonRows } from '../components/States'
import { TableContainer, Td, Th } from '../components/Table'
import { RecommendationTag } from '../components/Tag'
import { formatBRL, formatDate, formatDateTime, formatPct, formatRelative } from '../lib/format'
import { CHANNEL_LABEL, DECISION_LABEL, ROLE_LABEL } from '../lib/labels'
import { DecisionMix } from '../components/DecisionMix'
import { DECISION_FILL } from '../lib/decisionStyle'
import { initials } from '../lib/people'

const RECS: RecommendationType[] = ['SUBIR', 'BAIXAR', 'MANTER', 'REVISAR']
const PAGE_SIZE = 15

export function AnalystDetailPage() {
  const { id = '' } = useParams()
  const { data: a, isLoading, error } = useAnalyst(id)
  const [page, setPage] = useState(1)
  const [decision, setDecision] = useState<DecisionType | ''>('')
  const history = useDecisionHistory({
    user_id: id,
    decision: decision || undefined,
    page,
    page_size: PAGE_SIZE,
  })

  if (isLoading) return <Loading />
  if (error || !a) return <ErrorBox error={error} />
  const maxRec = Math.max(1, ...RECS.map((r) => a.by_recommendation[r]))
  const reasons = Object.entries(a.rejection_reasons).sort((x, y) => y[1] - x[1])

  return (
    <div className="space-y-4">
      <Breadcrumb items={[{ label: 'Analistas', to: '/analistas' }, { label: a.name }]} />
      <div className="flex items-center gap-3">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-brand-purple text-base font-bold text-white">
          {initials(a.name)}
        </span>
        <div className="flex-1">
          <PageHeader
            kicker={ROLE_LABEL[a.role]}
            title={a.name}
            description={
              a.last_activity_at
                ? `Última análise ${formatRelative(a.last_activity_at)} (${formatDateTime(a.last_activity_at)})`
                : 'Ainda não registrou análises.'
            }
            actions={
              <a
                href={`/api/decisions/export${buildQuery({ user_id: id })}`}
                download
                className={buttonClass('secondary')}
              >
                Exportar CSV
              </a>
            }
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <KpiCard
          label="Decisões registradas"
          value={a.decisions_total}
          target={`${a.rounds_count} rodada(s)`}
          met={null}
        />
        <KpiCard
          label="Últimos 7 dias"
          value={a.decisions_last_7_days}
          target="decisões"
          met={null}
        />
        <KpiCard
          label="Aceite pessoal"
          value={a.acceptance_rate === null ? '—' : formatPct(a.acceptance_rate)}
          target="referência do piloto ≥ 70%"
          met={a.acceptance_rate !== null && a.acceptance_rate >= 0.7}
          note={
            a.acceptance_base
              ? `sobre ${a.acceptance_base} SUBIR/BAIXAR decididas`
              : 'sem base de cálculo'
          }
        />
        <KpiCard
          label="Rejeições"
          value={a.by_decision.REJEITAR}
          target={`${a.by_decision.ADIAR} adiada(s)`}
          met={null}
        />
      </div>

      <div className="grid gap-3 lg:grid-cols-[3fr_2fr]">
        <Card title="Decisões por dia" subtitle="Últimos 30 dias">
          <DecisionsByDayChart data={a.decisions_by_day} height={200} />
        </Card>
        <Card title="Perfil das decisões">
          <DecisionMix byDecision={a.by_decision} total={a.decisions_total} />
          <h3 className="mb-1 mt-4 text-xs font-bold text-ink-muted">Por tipo de recomendação</h3>
          <ul className="space-y-1.5">
            {RECS.map((r) => (
              <li key={r} className="flex items-center gap-2 text-xs">
                <span className="w-16">
                  <RecommendationTag value={r} />
                </span>
                <span className="h-2.5 flex-1 rounded bg-brand-purpleLight">
                  <span
                    className="block h-full rounded bg-brand-purpleData"
                    style={{ width: `${(a.by_recommendation[r] / maxRec) * 100}%` }}
                  />
                </span>
                <span className="tabular w-6 text-right font-bold">{a.by_recommendation[r]}</span>
              </li>
            ))}
          </ul>
          <h3 className="mb-1 mt-4 text-xs font-bold text-ink-muted">Motivos de rejeição</h3>
          {reasons.length ? (
            <ul className="text-xs">
              {reasons.map(([reason, n]) => (
                <li key={reason} className="flex justify-between border-b border-line py-1">
                  {reason} <strong className="tabular">{n}</strong>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-ink-muted">Nenhuma rejeição.</p>
          )}
        </Card>
      </div>

      <Card
        title="Análises registradas"
        subtitle="Todas as decisões do analista, da mais recente para a mais antiga"
        action={
          <select
            aria-label="Filtrar por decisão"
            className="h-8 rounded border border-brand-purpleLine bg-brand-purpleLight px-2 text-[13px]"
            value={decision}
            onChange={(e) => {
              setDecision(e.target.value as DecisionType | '')
              setPage(1)
            }}
          >
            <option value="">Todas as decisões</option>
            {(Object.keys(DECISION_FILL) as DecisionType[]).map((t) => (
              <option key={t} value={t}>
                {DECISION_LABEL[t]}
              </option>
            ))}
          </select>
        }
      >
        <TableContainer>
          <thead>
            <tr>
              <Th>Data/hora</Th>
              <Th>SKU · Produto</Th>
              <Th>Canal</Th>
              <Th>Rodada</Th>
              <Th>Recomendação</Th>
              <Th numeric>Sugerido</Th>
              <Th>Decisão</Th>
              <Th numeric>Aplicado</Th>
              <Th>Motivo / comentário</Th>
            </tr>
          </thead>
          <tbody>
            {history.isLoading && <SkeletonRows cols={9} rows={5} />}
            {!history.isLoading && history.data?.items.length === 0 && (
              <tr>
                <td colSpan={9}>
                  <EmptyState title="Nenhuma análise registrada" />
                </td>
              </tr>
            )}
            {history.data?.items.map((d, i) => (
              <tr key={d.id} className={`border-b border-line ${i % 2 ? 'bg-zebra' : ''}`}>
                <Td className="tabular whitespace-nowrap">{formatDateTime(d.created_at)}</Td>
                <Td>
                  <Link
                    to={`/produtos/${d.sku}`}
                    className="font-semibold text-brand-purple hover:underline"
                  >
                    {d.sku}
                  </Link>{' '}
                  · {d.product_name}
                </Td>
                <Td className="whitespace-nowrap">{CHANNEL_LABEL[d.channel]}</Td>
                <Td className="tabular">{formatDate(d.round_date)}</Td>
                <Td>
                  <RecommendationTag value={d.snapshot_recommendation} />
                </Td>
                <Td numeric>{formatBRL(d.snapshot_suggested_price)}</Td>
                <Td>
                  <Link to={`/recomendacoes?item=${d.recommendation_id}`} className="inline-flex">
                    <span
                      className={`inline-flex h-5 items-center rounded-[10px] border px-2 text-[11px] font-bold ${DECISION_FILL[d.decision]}`}
                    >
                      {DECISION_LABEL[d.decision]}
                    </span>
                  </Link>
                </Td>
                <Td numeric>{formatBRL(d.applied_price)}</Td>
                <Td className="text-xs">
                  {[d.rejection_reason, d.comment].filter(Boolean).join(' · ') || '—'}
                </Td>
              </tr>
            ))}
          </tbody>
        </TableContainer>
        <Pagination
          page={page}
          pageSize={PAGE_SIZE}
          total={history.data?.total ?? 0}
          onChange={setPage}
        />
      </Card>
    </div>
  )
}
