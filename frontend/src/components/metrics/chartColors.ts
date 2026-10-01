import type { DecisionBucket, RecommendationType } from '../../api/types'

// Tokens da marca (UI_GUIDE). As cores de tag são claras: toda barra com cor de tag leva
// contorno e rótulo de texto, então a identidade nunca depende só da cor.
export const BRAND = {
  purple: '#5E3A85',
  purpleData: '#7B4FA8',
  purpleLine: '#D9CEE8',
  lime: '#B4C805',
  limeData: '#7E9A0A',
  ink: '#222222',
  muted: '#666666',
  line: '#E5E0EC',
}

export const RECOMMENDATION_FILL: Record<RecommendationType, string> = {
  SUBIR: '#DCEFD9',
  BAIXAR: '#FDE2E1',
  MANTER: '#EEEEEE',
  REVISAR: '#FFF2CC',
}

export const RECOMMENDATION_STROKE: Record<RecommendationType, string> = {
  SUBIR: '#8DBF82',
  BAIXAR: '#E39A95',
  MANTER: '#B5B5B5',
  REVISAR: '#DDBF5E',
}

export const BUCKET_FILL: Record<DecisionBucket, string> = {
  APROVADA: '#DCEFD9',
  EDITADA: '#FFF2CC',
  REJEITADA: '#FDE2E1',
  ADIADA: '#EEEEEE',
  PENDENTE: '#FFFFFF',
  SEM_ACAO: '#F7F5FA',
}

export const BUCKET_STROKE: Record<DecisionBucket, string> = {
  APROVADA: '#8DBF82',
  EDITADA: '#DDBF5E',
  REJEITADA: '#E39A95',
  ADIADA: '#B5B5B5',
  PENDENTE: '#999999',
  SEM_ACAO: '#D9CEE8',
}

export const BUCKET_LABEL: Record<DecisionBucket, string> = {
  APROVADA: 'Aprovada',
  EDITADA: 'Editada',
  REJEITADA: 'Rejeitada',
  ADIADA: 'Adiada',
  PENDENTE: 'Pendente',
  SEM_ACAO: 'Sem ação (MANTER)',
}

export const AXIS_TICK = { fill: BRAND.muted, fontSize: 12 }
