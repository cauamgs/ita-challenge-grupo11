import { Link } from 'react-router-dom'
import { useAnalysts } from '../api/platform'
import type { AnalystSummary } from '../api/types'
import { Card, PageHeader } from '../components/Card'
import { EmptyState, ErrorBox, Loading } from '../components/States'
import { formatDateTime, formatPct, formatRelative } from '../lib/format'
import { ROLE_LABEL } from '../lib/labels'
import { initials } from '../lib/people'
import { DecisionMix } from '../components/DecisionMix'

function AnalystCard({ a }: { a: AnalystSummary }) {
  return (
    <Card className="flex flex-col">
      <div className="flex items-center gap-3">
        <span className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-purple text-sm font-bold text-white">
          {initials(a.name)}
        </span>
        <div className="flex-1">
          <p className="text-[15px] font-bold text-brand-purple">{a.name}</p>
          <p className="text-xs text-ink-muted">
            {ROLE_LABEL[a.role]} ·{' '}
            {a.last_activity_at ? (
              <span title={formatDateTime(a.last_activity_at)}>
                última análise {formatRelative(a.last_activity_at)}
              </span>
            ) : (
              'sem análises ainda'
            )}
          </p>
        </div>
      </div>
      <dl className="mt-3 grid grid-cols-4 gap-2 text-center">
        {[
          ['Decisões', a.decisions_total],
          ['Últimos 7 dias', a.decisions_last_7_days],
          ['Rodadas', a.rounds_count],
          ['Aceite', a.acceptance_rate === null ? '—' : formatPct(a.acceptance_rate)],
        ].map(([label, value]) => (
          <div key={label as string} className="rounded-card bg-brand-purpleLight py-1.5">
            <dd className="tabular text-[18px] font-extrabold text-brand-purple">{value}</dd>
            <dt className="text-[11px] text-ink-muted">{label}</dt>
          </div>
        ))}
      </dl>
      <div className="mt-3 flex-1">
        <DecisionMix byDecision={a.by_decision} total={a.decisions_total} />
      </div>
      <Link
        to={`/analistas/${a.id}`}
        className="mt-3 self-start text-[13px] font-semibold text-brand-purple hover:underline"
      >
        Ver histórico de análises →
      </Link>
    </Card>
  )
}

export function AnalystsPage() {
  const { data, isLoading, error } = useAnalysts()
  if (isLoading) return <Loading />
  if (error || !data) return <ErrorBox error={error} />
  return (
    <div className="space-y-4">
      <PageHeader
        kicker="Equipe"
        title="Histórico de análises por analista"
        description="Volume de decisões, tipo de decisão, aceite pessoal (SUBIR/BAIXAR aprovadas ou editadas em até 1%) e atividade."
      />
      {data.length === 0 ? (
        <EmptyState title="Nenhum usuário cadastrado" />
      ) : (
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {data.map((a) => (
            <AnalystCard key={a.id} a={a} />
          ))}
        </div>
      )}
    </div>
  )
}
