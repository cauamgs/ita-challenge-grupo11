import { useRoundSummary } from '../../api/queries'
import { Callout } from '../States'

export function RoundSummaryBox({ roundId }: { roundId: string }) {
  const { data, isLoading, error } = useRoundSummary(roundId)
  return (
    <Callout tone="lime">
      <p className="text-[13px]" aria-live="polite">
        <strong className="text-brand-purpleDark">Resumo da rodada: </strong>
        {isLoading && <span className="text-ink-muted">carregando…</span>}
        {error && <span className="text-ink-muted">não foi possível carregar o resumo.</span>}
        {data && (
          <>
            {data.summary_text}{' '}
            <span className="text-ink-muted">
              · {data.decided} decididos · {data.pending} pendentes
            </span>
          </>
        )}
      </p>
    </Callout>
  )
}
