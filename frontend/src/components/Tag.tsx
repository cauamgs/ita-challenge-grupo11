import type {
  ItemStatus,
  PriceChangeType,
  RecommendationType,
  RiskLevel,
  SyncStatus,
  SyncTrigger,
} from '../api/types'
import { formatPct } from '../lib/format'
import {
  PRICE_CHANGE_LABEL,
  RECOMMENDATION_LABEL,
  RISK_LABEL,
  STATUS_LABEL,
  SYNC_STATUS_LABEL,
  SYNC_TRIGGER_LABEL,
} from '../lib/labels'

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

const SYNC_BG: Record<SyncStatus, string> = {
  SUCESSO: 'bg-tag-subir',
  ERRO: 'bg-tag-baixar',
  EM_ANDAMENTO: 'bg-tag-revisar',
}

export function SyncStatusTag({ value }: { value: SyncStatus }) {
  return <span className={`${base} ${SYNC_BG[value]}`}>{SYNC_STATUS_LABEL[value]}</span>
}

export function SyncTriggerTag({ value }: { value: SyncTrigger }) {
  return (
    <span className={`${base} border border-brand-purpleLine bg-brand-purpleLight`}>
      {SYNC_TRIGGER_LABEL[value]}
    </span>
  )
}

const CHANGE_BG: Record<PriceChangeType, string> = {
  AUMENTO: 'bg-tag-subir',
  REDUCAO: 'bg-tag-baixar',
  INICIAL: 'bg-tag-manter',
}
const CHANGE_ARROW: Record<PriceChangeType, string> = { AUMENTO: '↑ ', REDUCAO: '↓ ', INICIAL: '' }

export function PriceChangeTag({
  value,
  variation,
}: {
  value: PriceChangeType
  variation?: number | null
}) {
  return (
    <span className={`${base} ${CHANGE_BG[value]}`}>
      {CHANGE_ARROW[value]}
      {PRICE_CHANGE_LABEL[value]}
      {variation !== null && variation !== undefined && value !== 'INICIAL' && (
        <span className="ml-1 font-semibold">{formatPct(variation, { sign: true })}</span>
      )}
    </span>
  )
}
