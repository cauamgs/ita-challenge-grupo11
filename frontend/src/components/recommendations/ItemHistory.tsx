import type { RecommendationDetail } from '../../api/types'
import { formatBRL, formatDate, formatDateTime } from '../../lib/format'
import { DECISION_LABEL } from '../../lib/labels'
import { SectionTitle } from '../Drawer'

export function ItemHistory({ detail }: { detail: RecommendationDetail }) {
  return (
    <section>
      <SectionTitle>Histórico do item</SectionTitle>
      {detail.decision_history.length === 0 ? (
        <p className="text-xs text-ink-muted">
          Nenhuma decisão registrada para este SKU neste canal.
        </p>
      ) : (
        <ol className="space-y-2 border-l-2 border-brand-purpleLine pl-3">
          {detail.decision_history.map((d) => (
            <li key={d.id} className="text-[13px]">
              <p>
                <strong>{DECISION_LABEL[d.decision]}</strong>
                {d.applied_price !== null && <> · {formatBRL(d.applied_price)}</>}
                {d.rejection_reason && <> · {d.rejection_reason}</>}
              </p>
              <p className="text-xs text-ink-muted">
                {d.user_name} · {formatDateTime(d.created_at)} · rodada {formatDate(d.round_date)} ·
                recomendação {d.snapshot_recommendation} a {formatBRL(d.snapshot_suggested_price)}
              </p>
              {d.comment && <p className="text-xs italic">“{d.comment}”</p>}
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}
