import type { DecisionType } from '../api/types'
import { DECISION_FILL, DECISION_TYPES } from '../lib/decisionStyle'
import { DECISION_LABEL } from '../lib/labels'

export function DecisionMix({
  byDecision,
  total,
}: {
  byDecision: Record<DecisionType, number>
  total: number
}) {
  if (!total) return <p className="text-xs text-ink-muted">Nenhuma decisão registrada.</p>
  return (
    <div>
      <div className="flex h-3 gap-[2px] overflow-hidden rounded">
        {DECISION_TYPES.map(
          (t) =>
            byDecision[t] > 0 && (
              <div
                key={t}
                className={`h-full border ${DECISION_FILL[t]}`}
                style={{ width: `${(byDecision[t] / total) * 100}%` }}
                title={`${DECISION_LABEL[t]}: ${byDecision[t]}`}
              />
            ),
        )}
      </div>
      <ul className="mt-1.5 flex flex-wrap gap-x-3 text-[11px] text-ink">
        {DECISION_TYPES.map((t) => (
          <li key={t} className="flex items-center gap-1">
            <span className={`inline-block h-2 w-2 rounded-sm border ${DECISION_FILL[t]}`} />
            {DECISION_LABEL[t]} <strong className="tabular">{byDecision[t]}</strong>
          </li>
        ))}
      </ul>
    </div>
  )
}
