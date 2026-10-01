import { useState } from 'react'
import { ApiError } from '../../api/client'
import { useCreateDecision } from '../../api/mutations'
import type { DecisionType, RecommendationDetail } from '../../api/types'
import { useSession } from '../../app/session'
import { formatBRL, formatDateTime, formatPct, parsePrice } from '../../lib/format'
import { CHANNEL_LABEL, DECISION_LABEL, REJECTION_REASONS } from '../../lib/labels'
import { Button } from '../Button'
import { SectionTitle } from '../Drawer'
import { fieldClass, FieldLabel } from '../Field'
import { Modal } from '../Modal'
import { Callout } from '../States'
import { StatusTag } from '../Tag'
import { useToast } from '../Toast'

const DECIDED = new Set(['APROVADA', 'EDITADA', 'REJEITADA'])

function editWarnings(detail: RecommendationDetail, price: number | null): string[] {
  if (price === null || price <= 0) return []
  const warnings: string[] = []
  if (price < detail.min_price_floor)
    warnings.push(
      `Preço abaixo do piso de margem mínima (${formatBRL(detail.min_price_floor)}). Confirme antes de aplicar. (R01)`,
    )
  const variation = price / detail.current_price - 1
  if (Math.abs(variation) > 0.05)
    warnings.push(
      `Variação de ${formatPct(variation, { sign: true })} sobre o preço atual, acima do limite de 5% por decisão. (R02)`,
    )
  return warnings
}

export function DecisionPanel({ detail }: { detail: RecommendationDetail }) {
  const { currentUser } = useSession()
  const toast = useToast()
  const mutation = useCreateDecision(detail.id)
  const [redo, setRedo] = useState(false)
  const [comment, setComment] = useState('')
  const [modal, setModal] = useState<'EDITAR' | 'REJEITAR' | null>(null)
  const [priceText, setPriceText] = useState('')
  const [reason, setReason] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  const last = detail.last_decision
  const decided = DECIDED.has(detail.status)
  const showActions = !decided || redo
  const price = parsePrice(priceText)
  const warnings = editWarnings(detail, price)

  const submit = (
    decision: DecisionType,
    extra: { applied_price?: number; rejection_reason?: string } = {},
  ) => {
    if (!currentUser) return
    setFormError(null)
    mutation.mutate(
      { user_id: currentUser.id, decision, comment: comment.trim() || null, ...extra },
      {
        onSuccess: (result) => {
          toast({
            tone: result.warnings.length ? 'warning' : 'success',
            title: `Decisão registrada: ${DECISION_LABEL[decision]} (${detail.sku} · ${CHANNEL_LABEL[detail.channel]})`,
            lines: result.warnings,
          })
          setModal(null)
          setRedo(false)
          setComment('')
          setPriceText('')
          setReason('')
        },
        onError: (error) => {
          const message = error instanceof ApiError ? error.message : 'Não foi possível registrar.'
          if (modal) setFormError(message)
          else toast({ tone: 'error', title: message })
        },
      },
    )
  }

  const openEdit = () => {
    setFormError(null)
    setPriceText(detail.suggested_price.toFixed(2).replace('.', ','))
    setModal('EDITAR')
  }

  return (
    <section>
      <SectionTitle>Decisão</SectionTitle>

      {last && (decided || detail.status === 'ADIADA') && (
        <div className="mb-3 rounded-card border border-line p-3 text-sm">
          <div className="flex flex-wrap items-center gap-2">
            <StatusTag value={detail.status} />
            <span className="text-ink-muted">
              por <strong className="text-ink">{last.user_name}</strong> em{' '}
              {formatDateTime(last.created_at)}
            </span>
          </div>
          <dl className="mt-2 grid grid-cols-2 gap-x-6 gap-y-1 text-[13px]">
            {last.applied_price !== null && (
              <>
                <dt className="text-ink-muted">Preço aplicado</dt>
                <dd className="tabular">{formatBRL(last.applied_price)}</dd>
              </>
            )}
            {last.rejection_reason && (
              <>
                <dt className="text-ink-muted">Motivo</dt>
                <dd>{last.rejection_reason}</dd>
              </>
            )}
            {last.comment && (
              <>
                <dt className="text-ink-muted">Comentário</dt>
                <dd>{last.comment}</dd>
              </>
            )}
          </dl>
          {decided && !redo && (
            <Button variant="ghost" className="mt-3" onClick={() => setRedo(true)}>
              Refazer decisão
            </Button>
          )}
        </div>
      )}

      {detail.status === 'SEM_ACAO' && (
        <p className="mb-2 text-xs text-ink-muted">
          MANTER: nenhuma ação necessária. Se discordar, você pode editar o preço.
        </p>
      )}

      {showActions && (
        <div className="space-y-2">
          {redo && (
            <Callout tone="purple">
              <p className="text-xs">
                A nova decisão cria um novo registro; a anterior continua no histórico.
              </p>
            </Callout>
          )}
          <label className="block">
            <FieldLabel>Comentário (opcional)</FieldLabel>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              rows={2}
              className={`${fieldClass} h-auto w-full py-1.5`}
              placeholder="Observações para o registro"
            />
          </label>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="approve"
              disabled={mutation.isPending}
              onClick={() => submit('APROVAR')}
            >
              Aprovar {formatBRL(detail.suggested_price)}
            </Button>
            <Button variant="edit" disabled={mutation.isPending} onClick={openEdit}>
              Editar
            </Button>
            <Button
              variant="reject"
              disabled={mutation.isPending}
              onClick={() => {
                setFormError(null)
                setModal('REJEITAR')
              }}
            >
              Rejeitar
            </Button>
            <Button
              variant="postpone"
              disabled={mutation.isPending}
              onClick={() => submit('ADIAR')}
            >
              Adiar
            </Button>
            {redo && (
              <Button variant="ghost" onClick={() => setRedo(false)}>
                Cancelar
              </Button>
            )}
          </div>
          <p className="text-xs text-ink-muted">
            Registrando como <strong>{currentUser?.name ?? '—'}</strong>.
          </p>
        </div>
      )}

      <Modal
        open={modal === 'EDITAR'}
        title={`Editar preço · ${detail.sku}`}
        onClose={() => setModal(null)}
        footer={
          <>
            <Button variant="ghost" onClick={() => setModal(null)}>
              Cancelar
            </Button>
            <Button
              disabled={mutation.isPending}
              onClick={() => {
                if (price === null) return setFormError('Informe o novo preço.')
                if (price <= 0) return setFormError('O preço deve ser maior que zero.')
                submit('EDITAR', { applied_price: price })
              }}
            >
              {warnings.length ? 'Confirmar mesmo assim' : 'Salvar edição'}
            </Button>
          </>
        }
      >
        <p className="text-xs text-ink-muted">
          Atual {formatBRL(detail.current_price)} · sugerido {formatBRL(detail.suggested_price)} ·
          piso {formatBRL(detail.min_price_floor)}
        </p>
        <label className="block">
          <FieldLabel>Novo preço (R$)</FieldLabel>
          <input
            inputMode="decimal"
            value={priceText}
            onChange={(e) => {
              setPriceText(e.target.value)
              setFormError(null)
            }}
            className={`${fieldClass} tabular w-40`}
            aria-invalid={!!formError}
          />
          {price !== null && price > 0 && (
            <span className="ml-2 text-xs text-ink-muted">
              {formatPct(price / detail.current_price - 1, { sign: true })} sobre o atual
            </span>
          )}
        </label>
        {warnings.map((w) => (
          <div
            key={w}
            className="rounded-card border-l-4 border-[#E5C04B] bg-tag-revisar px-3 py-2 text-xs"
          >
            {w}
          </div>
        ))}
        {formError && <p className="text-xs font-semibold text-[#B3261E]">{formError}</p>}
      </Modal>

      <Modal
        open={modal === 'REJEITAR'}
        title={`Rejeitar · ${detail.sku}`}
        onClose={() => setModal(null)}
        footer={
          <>
            <Button variant="ghost" onClick={() => setModal(null)}>
              Cancelar
            </Button>
            <Button
              variant="reject"
              disabled={mutation.isPending}
              onClick={() => {
                if (!reason) return setFormError('Selecione o motivo da rejeição.')
                submit('REJEITAR', { rejection_reason: reason })
              }}
            >
              Rejeitar recomendação
            </Button>
          </>
        }
      >
        <label className="block">
          <FieldLabel>Motivo (obrigatório)</FieldLabel>
          <select
            value={reason}
            onChange={(e) => {
              setReason(e.target.value)
              setFormError(null)
            }}
            className={`${fieldClass} w-full`}
          >
            <option value="">Selecione…</option>
            {REJECTION_REASONS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>
        <label className="block">
          <FieldLabel>Comentário (opcional)</FieldLabel>
          <textarea
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={2}
            className={`${fieldClass} h-auto w-full py-1.5`}
          />
        </label>
        {formError && <p className="text-xs font-semibold text-[#B3261E]">{formError}</p>}
      </Modal>
    </section>
  )
}
