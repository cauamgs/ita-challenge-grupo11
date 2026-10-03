import { Link } from 'react-router-dom'
import { useDashboard } from '../api/platform'
import type { Dashboard } from '../api/types'
import { useSession } from '../app/session'
import { buttonClass } from '../components/Button'
import { Card, PageHeader, QuickAction } from '../components/Card'
import { DecisionsByDayChart, PriceChangesChart } from '../components/charts/PlatformCharts'
import { KpiCard } from '../components/metrics/KpiCard'
import { EmptyState, ErrorBox, Loading } from '../components/States'
import { RecommendationTag, StatusTag, SyncStatusTag } from '../components/Tag'
import {
  formatBRL,
  formatDate,
  formatDateTime,
  formatNumber,
  formatPct,
  formatRelative,
  formatWeekdayDateTime,
  plural,
} from '../lib/format'
import { CHANNEL_LABEL, ROLE_LABEL } from '../lib/labels'

function greeting(): string {
  const hour = new Date().getHours()
  return hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite'
}

function pct(value: number | null): string {
  return value === null ? '—' : formatPct(value)
}

function hours(value: number | null): string {
  const h = value ?? 0
  return h < 1 ? `${Math.round(h * 60)} min` : `${formatNumber(h)} h`
}

function RoundProgressBar({ round }: { round: NonNullable<Dashboard['round']> }) {
  const segments = [
    { key: 'Decididos', value: round.decided, cls: 'bg-brand-purpleData' },
    { key: 'Adiados', value: round.postponed, cls: 'bg-[#C9B8DE]' },
    {
      key: 'Pendentes',
      value: round.pending - round.postponed,
      cls: 'bg-brand-purpleLight border border-brand-purpleLine',
    },
    { key: 'Sem ação (MANTER)', value: round.no_action, cls: 'bg-[#EEEEEE]' },
  ]
  const done = round.total ? round.decided / (round.total - round.no_action || 1) : 0
  return (
    <div>
      <div className="flex items-baseline justify-between">
        <p className="text-[13px]">
          <span className="tabular text-[26px] font-extrabold text-brand-purple">
            {formatPct(done)}
          </span>{' '}
          <span className="text-ink-muted">
            das recomendações que pedem ação já foram decididas
          </span>
        </p>
        <span className="tabular text-xs text-ink-muted">
          {round.decided} de {round.total - round.no_action}
        </span>
      </div>
      <div
        className="mt-2 flex h-4 w-full gap-[2px] overflow-hidden rounded"
        role="img"
        aria-label="Progresso da rodada"
      >
        {segments.map(
          (s) =>
            s.value > 0 && (
              <div
                key={s.key}
                className={`${s.cls} h-full first:rounded-l last:rounded-r`}
                style={{ width: `${(s.value / round.total) * 100}%` }}
                title={`${s.key}: ${s.value}`}
              />
            ),
        )}
      </div>
      <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink">
        {segments.map((s) => (
          <li key={s.key} className="flex items-center gap-1.5">
            <span className={`inline-block h-2.5 w-2.5 rounded-sm ${s.cls}`} />
            {s.key} <strong className="tabular">{s.value}</strong>
          </li>
        ))}
      </ul>
      <div className="mt-3 grid grid-cols-4 gap-2 text-center">
        {(['SUBIR', 'BAIXAR', 'MANTER', 'REVISAR'] as const).map((r) => (
          <Link
            key={r}
            to={`/recomendacoes?recomendacao=${r}`}
            className="rounded-card border border-line py-2 hover:bg-brand-purpleLight"
          >
            <RecommendationTag value={r} />
            <p className="tabular mt-1 text-[18px] font-bold text-brand-purple">
              {round.by_recommendation[r]}
            </p>
          </Link>
        ))}
      </div>
    </div>
  )
}

export function DashboardPage() {
  const { currentUser, currentRound } = useSession()
  const { data: d, isLoading, error } = useDashboard(currentRound?.id)

  if (isLoading) return <Loading label="Montando o painel…" />
  if (error || !d) return <ErrorBox error={error} />

  const { round, kpis, erp } = d
  const first = currentUser?.name.split(' ')[0]
  const lastSync = erp.last_sync

  return (
    <div className="space-y-4">
      <PageHeader
        kicker="Início"
        title={`${greeting()}${first ? `, ${first}` : ''}`}
        description={
          round ? (
            <>
              Rodada de <strong>{formatDate(round.round_date)}</strong> · {round.pending} itens
              pendentes de análise
            </>
          ) : (
            'Nenhuma rodada de recomendações importada ainda.'
          )
        }
        actions={
          <>
            <Link to="/erp" className={buttonClass('ghost')}>
              Integração ERP
            </Link>
            <Link to="/recomendacoes?status=PENDENTE" className={buttonClass('primary')}>
              Analisar pendentes
            </Link>
          </>
        }
      />

      {/* Situação da base do ERP */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-card border-l-4 border-brand-lime bg-brand-limeLight px-3 py-2 text-[13px]">
        <strong className="text-brand-purpleDark">Base de produtos (ERP):</strong>
        {lastSync ? (
          <>
            <span className="flex items-center gap-1.5">
              <SyncStatusTag value={lastSync.status} /> última sincronização{' '}
              {formatRelative(lastSync.started_at)} ({formatDateTime(lastSync.started_at)})
            </span>
            <span className="text-ink-muted">
              {erp.products} produtos · referência {formatDate(erp.last_reference_date)}
            </span>
          </>
        ) : (
          <span>nunca sincronizada</span>
        )}
        <span className="text-ink-muted">
          {erp.schedule.enabled
            ? `Próxima automática: ${formatWeekdayDateTime(erp.schedule.next_run_at)}`
            : 'Sincronização automática desligada'}
        </span>
        <Link to="/erp" className="ml-auto font-semibold text-brand-purple hover:underline">
          Gerenciar →
        </Link>
      </div>

      {/* Indicadores */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-5">
        <KpiCard
          label="Pendentes na rodada"
          value={round ? round.pending : '—'}
          target={
            round
              ? `${plural(round.decided, 'decidido', 'decididos')} · ${plural(round.postponed, 'adiado', 'adiados')}`
              : 'sem rodada'
          }
          met={round ? round.pending === 0 : null}
        />
        <KpiCard
          label="Aceite das recomendações"
          value={kpis ? pct(kpis.acceptance_rate.value) : '—'}
          target="meta ≥ 70%"
          met={kpis?.acceptance_rate.value != null && kpis.acceptance_rate.value >= 0.7}
          note={
            kpis?.acceptance_rate.denominator
              ? `${kpis.acceptance_rate.numerator} de ${kpis.acceptance_rate.denominator}`
              : 'nenhuma decisão'
          }
        />
        <KpiCard
          label="SKUs na faixa competitiva"
          value={kpis ? pct(kpis.in_competitive_band.value) : '—'}
          target="meta ≥ 80%"
          met={kpis?.in_competitive_band.value != null && kpis.in_competitive_band.value >= 0.8}
        />
        <KpiCard
          label="Margem bruta média"
          value={kpis ? pct(kpis.avg_gross_margin.value) : '—'}
          target="meta ≥ 32,5%"
          met={kpis?.avg_gross_margin.value != null && kpis.avg_gross_margin.value >= 0.325}
        />
        <KpiCard
          label="Alterações de preço (90 dias)"
          value={
            <span>
              ↑{d.price_changes_90d.AUMENTO} <span className="text-ink-faint">/</span> ↓
              {d.price_changes_90d.REDUCAO}
            </span>
          }
          target="aumentos / reduções no ERP"
          met={null}
          note={kpis ? `revisão estimada: ${hours(kpis.estimated_review_hours.value)}` : undefined}
        />
      </div>

      {/* Atalhos para as análises */}
      <Card title="Ir para as análises" subtitle="Atalhos com os filtros já aplicados">
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          <QuickAction
            to="/recomendacoes?risco=ALTO&status=PENDENTE"
            count={round?.high_risk_pending ?? '—'}
            label="Revisar itens de alto risco"
            hint="pendentes com risco Alto"
            tone="alert"
          />
          <QuickAction
            to="/recomendacoes?aprovacao=1&status=PENDENTE"
            count={round?.requires_approval_pending ?? '—'}
            label="Exigem aprovação de gestor"
            hint="curva A, campanha, alto risco…"
          />
          <QuickAction
            to="/recomendacoes?ordem=value_at_stake&dir=desc&status=PENDENTE"
            count={round?.pending ?? '—'}
            label="Maior valor em jogo"
            hint="pendentes, do maior para o menor R$/mês"
            tone="lime"
          />
          <QuickAction
            to="/metricas"
            label="Métricas da carteira"
            hint="aceite, faixa competitiva, margem e gráficos"
          />
          <QuickAction
            to="/produtos?ordem=recentes"
            count={d.price_changes_90d.AUMENTO + d.price_changes_90d.REDUCAO}
            label="Histórico de preços dos SKUs"
            hint="aumentos e reduções vindos do ERP"
          />
          <QuickAction
            to="/analistas"
            label="Análises por analista"
            hint="volume, aceite e atividade de cada um"
          />
        </div>
      </Card>

      <div className="grid gap-3 lg:grid-cols-2">
        <Card
          title="Progresso da rodada"
          subtitle={round ? `Rodada de ${formatDate(round.round_date)}` : undefined}
          action={
            round && (
              <Link
                to="/recomendacoes"
                className="text-xs font-semibold text-brand-purple hover:underline"
              >
                Abrir lista →
              </Link>
            )
          }
        >
          {round ? (
            <RoundProgressBar round={round} />
          ) : (
            <EmptyState title="Nenhuma rodada importada">
              <Link to="/recomendacoes" className="font-semibold text-brand-purple hover:underline">
                Importe uma rodada de recomendações
              </Link>
            </EmptyState>
          )}
        </Card>
        <Card title="Decisões registradas" subtitle="Últimos 14 dias, todos os analistas">
          <DecisionsByDayChart data={d.decisions_by_day} />
        </Card>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <Card
          title="Alterações de preço no ERP"
          subtitle="Aumentos e reduções por mês (últimos 6 meses)"
          action={
            <Link
              to="/produtos?ordem=recentes"
              className="text-xs font-semibold text-brand-purple hover:underline"
            >
              Ver produtos →
            </Link>
          }
        >
          <PriceChangesChart data={d.price_changes_by_month} />
        </Card>
        <Card title="Pendentes com maior valor em jogo" subtitle="Comece por aqui">
          {d.top_pending.length === 0 ? (
            <EmptyState title={round ? 'Nada pendente com valor em jogo' : 'Sem rodada'} />
          ) : (
            <ul className="divide-y divide-line">
              {d.top_pending.map((t) => (
                <li key={t.recommendation_id}>
                  <Link
                    to={`/recomendacoes?item=${t.recommendation_id}`}
                    className="flex items-center gap-3 px-1 py-2 hover:bg-brand-purpleLight"
                  >
                    <RecommendationTag value={t.recommendation} />
                    <span className="flex-1 text-[13px]">
                      <strong>{t.sku}</strong> · {t.product_name}
                      <span className="block text-xs text-ink-muted">
                        {CHANNEL_LABEL[t.channel]} · {formatPct(t.variation, { sign: true })}
                      </span>
                    </span>
                    <span className="tabular text-right text-[13px] font-semibold">
                      {formatBRL(t.value_at_stake)}
                      <span className="block text-[11px] font-normal text-ink-muted">por mês</span>
                    </span>
                    <StatusTag value={t.status} />
                  </Link>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <div className="grid gap-3 lg:grid-cols-[3fr_2fr]">
        <Card title="Atividade recente" subtitle="Decisões e sincronizações">
          {d.recent_activity.length === 0 ? (
            <EmptyState title="Nenhuma atividade ainda" />
          ) : (
            <ol className="space-y-2">
              {d.recent_activity.map((a, i) => (
                <li key={i} className="flex gap-3">
                  <span
                    aria-hidden
                    className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${a.kind === 'SYNC' ? 'bg-brand-lime' : 'bg-brand-purpleData'}`}
                  />
                  <div className="flex-1 text-[13px]">
                    {a.link ? (
                      <Link
                        to={a.link}
                        className="font-semibold hover:text-brand-purple hover:underline"
                      >
                        {a.title}
                      </Link>
                    ) : (
                      <span className="font-semibold">{a.title}</span>
                    )}
                    {a.detail && <p className="text-xs text-ink-muted">{a.detail}</p>}
                  </div>
                  <span
                    className="whitespace-nowrap text-xs text-ink-muted"
                    title={formatDateTime(a.at)}
                  >
                    {formatRelative(a.at)}
                  </span>
                </li>
              ))}
            </ol>
          )}
        </Card>
        <Card
          title="Analistas"
          subtitle="Decisões na rodada e no total"
          action={
            <Link
              to="/analistas"
              className="text-xs font-semibold text-brand-purple hover:underline"
            >
              Ver histórico →
            </Link>
          }
        >
          <ul className="divide-y divide-line">
            {d.analysts.map((a) => (
              <li key={a.id}>
                <Link
                  to={`/analistas/${a.id}`}
                  className="flex items-center gap-3 px-1 py-2 hover:bg-brand-purpleLight"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-purpleLight text-xs font-bold text-brand-purple">
                    {a.name
                      .split(' ')
                      .map((p) => p[0])
                      .slice(0, 2)
                      .join('')}
                  </span>
                  <span className="flex-1 text-[13px]">
                    <strong>{a.name}</strong>
                    <span className="block text-xs text-ink-muted">{ROLE_LABEL[a.role]}</span>
                  </span>
                  <span className="tabular text-right text-[13px]">
                    <strong>{a.decisions_round}</strong> na rodada
                    <span className="block text-xs text-ink-muted">
                      {a.decisions_total} no total
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  )
}
