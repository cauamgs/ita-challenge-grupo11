import type { DecisionType } from '../api/types'

/** Cores das decisões (fundo + contorno), alinhadas às etiquetas. */
export const DECISION_FILL: Record<DecisionType, string> = {
  APROVAR: 'bg-tag-subir border-[#8DBF82]',
  EDITAR: 'bg-tag-revisar border-[#DDBF5E]',
  REJEITAR: 'bg-tag-baixar border-[#E39A95]',
  ADIAR: 'bg-tag-manter border-[#B5B5B5]',
}
export const DECISION_TYPES: DecisionType[] = ['APROVAR', 'EDITAR', 'REJEITAR', 'ADIAR']

/** Barra empilhada por tipo de decisão, com legenda escrita (cor nunca sozinha). */
