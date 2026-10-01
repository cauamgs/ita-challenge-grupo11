import type { ItemStatus, RecommendationType, RiskLevel } from '../api/types'
import { RECOMMENDATION_LABEL, RISK_LABEL, STATUS_LABEL } from '../lib/labels'

const base =
  'inline-flex h-5 items-center whitespace-nowrap rounded-[10px] px-2 text-[11px] font-bold leading-none text-ink'

const RECOMMENDATION_BG: Record<RecommendationType, string> = {
  SUBIR: 'bg-tag-subir',
  BAIXAR: 'bg-tag-baixar',
  MANTER: 'bg-tag-manter',
  REVISAR: 'bg-tag-revisar',
}

const RISK_BG: Record<RiskLevel, string> = {
  BAIXO: 'bg-tag-riscoBaixo',
  MEDIO: 'bg-tag-riscoMedio',
  ALTO: 'bg-tag-riscoAlto',
}

const STATUS_CLASS: Record<ItemStatus, string> = {
  PENDENTE: 'border border-ink-faint bg-transparent',
  ADIADA: 'bg-tag-manter',
  APROVADA: 'bg-tag-subir',
  EDITADA: 'bg-tag-revisar',
  REJEITADA: 'bg-tag-baixar',
  SEM_ACAO: 'border border-dashed border-line bg-transparent font-semibold text-ink-muted',
}

export function RecommendationTag({ value }: { value: RecommendationType }) {
  return (
    <span className={`${base} ${RECOMMENDATION_BG[value]}`}>{RECOMMENDATION_LABEL[value]}</span>
  )
}

export function RiskTag({ value }: { value: RiskLevel }) {
  return <span className={`${base} ${RISK_BG[value]}`}>{RISK_LABEL[value]}</span>
}

export function StatusTag({ value }: { value: ItemStatus }) {
  return (
    <span
      className={`${base} ${STATUS_CLASS[value]}`}
      title={value === 'SEM_ACAO' ? 'MANTER sem decisão: nenhuma ação necessária' : undefined}
    >
      {STATUS_LABEL[value]}
    </span>
  )
}
