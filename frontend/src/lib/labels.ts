import type { Channel, DecisionType, ItemStatus, RecommendationType, RiskLevel } from '../api/types'

export const CHANNEL_LABEL: Record<Channel, string> = {
  LOJA_FISICA: 'Loja física',
  ECOMMERCE: 'E-commerce',
  MARKETPLACE: 'Marketplace',
}

export const RECOMMENDATION_LABEL: Record<RecommendationType, string> = {
  SUBIR: 'SUBIR',
  BAIXAR: 'BAIXAR',
  MANTER: 'MANTER',
  REVISAR: 'REVISAR',
}

export const RISK_LABEL: Record<RiskLevel, string> = {
  BAIXO: 'Baixo',
  MEDIO: 'Médio',
  ALTO: 'Alto',
}

export const STATUS_LABEL: Record<ItemStatus, string> = {
  PENDENTE: 'Pendente',
  ADIADA: 'Adiada',
  APROVADA: 'Aprovada',
  EDITADA: 'Editada',
  REJEITADA: 'Rejeitada',
  SEM_ACAO: 'Sem ação',
}

export const DECISION_LABEL: Record<DecisionType, string> = {
  APROVAR: 'Aprovada',
  EDITAR: 'Editada',
  REJEITAR: 'Rejeitada',
  ADIAR: 'Adiada',
}

export const ROLE_LABEL = { ANALISTA: 'Analista', GESTOR: 'Gestora' } as const

export const REJECTION_REASONS = [
  'Discordo da referência de mercado',
  'Estoque/reposição',
  'Estratégia comercial',
  'Dados incorretos',
  'Outro',
] as const
