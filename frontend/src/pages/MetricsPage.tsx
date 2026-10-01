import { useRoundMetrics } from '../api/queries'
import type { MetricValue } from '../api/types'
import { useSession } from '../app/session'
import { Select } from '../components/Field'
import { ChartCard } from '../components/metrics/ChartCard'
import {
  DecisionsChart,
  DistributionChart,
  PriceIndexChart,
  RejectionReasonsChart,
} from '../components/metrics/Charts'
import { KpiCard } from '../components/metrics/KpiCard'
import { EmptyState, ErrorBox, Loading } from '../components/States'
import { TableContainer, Td, Th } from '../components/Table'
import { RecommendationTag, StatusTag } from '../components/Tag'
import { formatBRL, formatDate, formatNumber, formatPct } from '../lib/format'
import { CHANNEL_LABEL } from '../lib/labels'
import { useUrlState } from '../lib/useUrlState'
import { Link } from 'react-router-dom'

function formatHours(hours: number): string {
  return hours < 1 ? `${Math.round(hours * 60)} min` : `${formatNumber(hours)} h`
}

function pctValue(m: MetricValue): string {
  return m.value === null ? '—' : formatPct(m.value)
}

export function MetricsPage() {
  const { currentRound, rounds, setCurrentRoundId, isLoading: sessionLoading } = useSession()
  const url = useUrlState()
  const channel = url.get('canal') || undefined
  const curve = url.get('curva') || undefined
  const {
    data: m,
    isLoading,
    error,
    isFetching,
  } = useRoundMetrics(currentRound?.id, channel, curve)

  if (sessionLoading) return <Loading />
  if (!currentRound)
    return (
      <EmptyState title="Nenhuma rodada importada">
        As métricas aparecem depois que uma rodada for importada.
      </EmptyState>
    )

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Select
          label="Rodada"
          value={currentRound.id}
          onChange={(e) => setCurrentRoundId(e.target.value)}
        >
          {rounds.map((r) => (
            <option key={r.id} value={r.id}>
              Rodada {formatDate(r.round_date)}
            </option>
          ))}
        </Select>
        <Select
          label="Canal"
          value={channel ?? ''}
          onChange={(e) => url.set({ canal: e.target.value })}
        >
          <option value="">Canal: todos</option>
          <option value="LOJA_FISICA">Loja física</option>
          <option value="ECOMMERCE">E-commerce</option>
          <option value="MARKETPLACE">Marketplace</option>
        </Select>
        <Select
          label="Curva ABC"
          value={curve ?? ''}
          onChange={(e) => url.set({ curva: e.target.value })}
        >
          <option value="">Curva: todas</option>
          <option value="A">Curva A</option>
          <option value="B">Curva B</option>
          <option value="C">Curva C</option>
        </Select>
        {m && (
          <span className="text-xs text-ink-muted" aria-live="polite">
            {isFetching ? 'Atualizando…' : `${m.items} itens considerados`}
          </span>
        )}
      </div>

      {error && <ErrorBox error={error} />}
      {isLoading && <Loading label="Calculando métricas…" />}

      {m && (
        <>
          <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
            <KpiCard
              label="Aceite das recomendações"
              value={pctValue(m.acceptance_rate)}
              target="meta ≥ 70%"
              met={
                m.acceptance_rate.value !== null &&
                m.acceptance_rate.value >= m.acceptance_rate.target
              }
              note={
                m.acceptance_rate.denominator
                  ? `${m.acceptance_rate.numerator} de ${m.acceptance_rate.denominator} SUBIR/BAIXAR decididas`
                  : 'nenhuma decisão registrada'
              }
            />
            <KpiCard
              label="Tempo de revisão (estimado)"
              value={formatHours(m.estimated_review_hours.value ?? 0)}
              target="meta ≤ 6 h/semana"
              met={(m.estimated_review_hours.value ?? 0) <= m.estimated_review_hours.target}
              note={`${m.estimated_review_hours.numerator ?? 0} itens decididos × 2 min`}
            />
            <KpiCard
              label="SKUs na faixa competitiva (±2%)"
              value={pctValue(m.in_competitive_band)}
              target="meta ≥ 80%"
              met={
                m.in_competitive_band.value !== null &&
                m.in_competitive_band.value >= m.in_competitive_band.target
              }
              note={`${m.in_competitive_band.numerator} de ${m.in_competitive_band.denominator} SKU × canal`}
            />
            <KpiCard
              label="Margem bruta média"
              value={pctValue(m.avg_gross_margin)}
              target="meta ≥ 32,5%"
              met={
                m.avg_gross_margin.value !== null &&
                m.avg_gross_margin.value >= m.avg_gross_margin.target
              }
              note="ponderada pela receita mensal estimada"
            />
            <KpiCard
              label="Taxa de reversão"
              value="—"
              target="meta ≤ 3%"
              met={null}
              note="não disponível na v1"
            />
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <ChartCard
              title="Distribuição das recomendações"
              subtitle="Itens por tipo de recomendação"
            >
              <DistributionChart data={m.recommendation_distribution} />
            </ChartCard>
            <ChartCard
              title="Índice de preço por curva"
              subtitle="Média de preço atual ÷ preço de mercado × 100 (acima de 100 = mais caro que o mercado)"
            >
              <PriceIndexChart data={m.price_index_by_curve} />
            </ChartCard>
            <ChartCard title="Decisões do analista" subtitle="Situação das recomendações por tipo">
              <DecisionsChart data={m.decisions_by_recommendation} />
            </ChartCard>
            <ChartCard title="Motivos de rejeição" subtitle="Decisões vigentes de rejeição">
              <RejectionReasonsChart data={m.rejection_reasons} />
            </ChartCard>
          </div>

          <section>
            <h2 className="mb-2 text-[15px] font-bold text-brand-purple">
              Top 10 por valor em jogo
            </h2>
            <TableContainer>
              <thead>
                <tr>
                  <Th>SKU</Th>
                  <Th>Produto</Th>
                  <Th>Canal</Th>
                  <Th>Recomendação</Th>
                  <Th numeric>Variação</Th>
                  <Th numeric>Valor em jogo</Th>
                  <Th>Decisão</Th>
                </tr>
              </thead>
              <tbody>
                {m.top_value_at_stake.length === 0 && (
                  <tr>
                    <td colSpan={7}>
                      <EmptyState title="Nenhum item com valor em jogo para os filtros" />
                    </td>
                  </tr>
                )}
                {m.top_value_at_stake.map((t, i) => (
                  <tr
                    key={t.recommendation_id}
                    className={`border-b border-line ${i % 2 ? 'bg-zebra' : ''}`}
                  >
                    <Td>
                      <Link
                        to={`/recomendacoes?item=${t.recommendation_id}`}
                        className="font-semibold text-brand-purple hover:underline"
                      >
                        {t.sku}
                      </Link>
                    </Td>
                    <Td>{t.product_name}</Td>
                    <Td>{CHANNEL_LABEL[t.channel]}</Td>
                    <Td>
                      <RecommendationTag value={t.recommendation} />
                    </Td>
                    <Td numeric>{formatPct(t.variation, { sign: true })}</Td>
                    <Td numeric>{formatBRL(t.value_at_stake)}/mês</Td>
                    <Td>
                      <StatusTag value={t.status} />
                    </Td>
                  </tr>
                ))}
              </tbody>
            </TableContainer>
          </section>
        </>
      )}
    </div>
  )
}
