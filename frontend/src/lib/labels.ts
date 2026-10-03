import type {
  Channel,
  DecisionType,
  ItemStatus,
  PriceChangeType,
  RecommendationType,
  RiskLevel,
  SyncFrequency,
  SyncStatus,
  SyncTrigger,
} from '../api/types'

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

export const SYNC_TRIGGER_LABEL: Record<SyncTrigger, string> = {
  INICIAL: 'Carga inicial',
  MANUAL: 'Manual',
  AGENDADO: 'Automática',
  ARQUIVO: 'Arquivo',
}

export const SYNC_STATUS_LABEL: Record<SyncStatus, string> = {
  SUCESSO: 'Sucesso',
  ERRO: 'Erro',
  EM_ANDAMENTO: 'Em andamento',
}

export const FREQUENCY_LABEL: Record<SyncFrequency, string> = {
  DIARIA: 'Diária',
  SEMANAL: 'Semanal',
  MENSAL: 'Mensal',
}

export const WEEKDAY_LABEL = [
  'Segunda-feira',
  'Terça-feira',
  'Quarta-feira',
  'Quinta-feira',
  'Sexta-feira',
  'Sábado',
  'Domingo',
]

export const PRICE_CHANGE_LABEL: Record<PriceChangeType, string> = {
  AUMENTO: 'Aumento',
  REDUCAO: 'Redução',
  INICIAL: 'Registro inicial',
}

export const PRICE_SOURCE_LABEL = {
  ERP_HISTORICO: 'Histórico do ERP',
  ERP_SYNC: 'Sincronização',
} as const
