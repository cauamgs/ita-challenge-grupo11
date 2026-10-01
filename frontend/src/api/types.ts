export type Channel = 'LOJA_FISICA' | 'ECOMMERCE' | 'MARKETPLACE'
export type RecommendationType = 'SUBIR' | 'BAIXAR' | 'MANTER' | 'REVISAR'
export type RiskLevel = 'BAIXO' | 'MEDIO' | 'ALTO'
export type DecisionType = 'APROVAR' | 'EDITAR' | 'REJEITAR' | 'ADIAR'
export type ItemStatus = 'PENDENTE' | 'ADIADA' | 'APROVADA' | 'EDITADA' | 'REJEITADA' | 'SEM_ACAO'
export type UserRole = 'ANALISTA' | 'GESTOR'

export interface Page<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface User {
  id: string
  name: string
  role: UserRole
}

export interface Round {
  id: string
  round_date: string
  source: string
  created_at: string
  counts: Record<RecommendationType | 'total', number>
}

export interface RoundSummary {
  round_id: string
  round_date: string
  total: number
  with_change: number
  by_recommendation: Record<RecommendationType, number>
  review_reasons: Record<'campanha' | 'cobertura_curta' | 'dados_frageis' | 'outros', number>
  requires_approval: number
  top_value_at_stake: {
    recommendation_id: string
    sku: string
    product: string
    channel: Channel
    value: number
  } | null
  decided: number
  pending: number
  summary_text: string
}

export interface Decision {
  id: string
  recommendation_id: string
  round_date: string | null
  user_id: string
  user_name: string
  decision: DecisionType
  applied_price: number | null
  rejection_reason: string | null
  comment: string | null
  snapshot_recommendation: RecommendationType
  snapshot_suggested_price: number
  snapshot_current_price: number
  created_at: string
}

export interface RecommendationItem {
  id: string
  priority: number
  sku: string
  product_name: string
  category: string
  abc_curve: 'A' | 'B' | 'C'
  channel: Channel
  current_price: number
  market_price: number | null
  recommendation: RecommendationType
  suggested_price: number
  variation: number
  resulting_margin: number
  risk_level: RiskLevel
  requires_approval: boolean
  value_at_stake: number | null
  status: ItemStatus
  last_decision: Decision | null
}

export interface RecommendationDetail extends RecommendationItem {
  round_id: string
  round_date: string
  lowest_valid_competitor: number | null
  cost: number
  current_margin: number
  min_margin: number
  target_margin: number
  net_margin: number | null
  stock_qty: number | null
  coverage_days: number | null
  sales_trend_month: number | null
  sales_var_12m: number | null
  risk_score: number | null
  data_confidence: number | null
  est_monthly_revenue: number | null
  est_monthly_impact: number | null
  justification: string
  review_reasons: string[]
  data_alerts: string[]
  min_price_floor: number
  product: {
    sku: string
    name: string
    category: string
    brand: string
    abc_curve: string
    status: string
    is_strategic: boolean
  }
  decision_history: Decision[]
}

export interface RecommendationFilters {
  channel?: Channel
  abc_curve?: 'A' | 'B' | 'C'
  recommendation?: RecommendationType
  risk_level?: RiskLevel
  status?: 'PENDENTE' | 'DECIDIDO'
  requires_approval?: boolean
  q?: string
  sort?: 'priority' | 'variation' | 'value_at_stake' | 'risk'
  order?: 'asc' | 'desc'
  page?: number
  page_size?: number
}

export interface DecisionInput {
  user_id: string
  decision: DecisionType
  applied_price?: number | null
  rejection_reason?: string | null
  comment?: string | null
}

export interface DecisionCreated {
  decision: Decision
  warnings: string[]
}

export interface MetricValue {
  value: number | null
  target: number
  numerator: number | null
  denominator: number | null
  note: string | null
}

export type DecisionBucket =
  'APROVADA' | 'EDITADA' | 'REJEITADA' | 'ADIADA' | 'PENDENTE' | 'SEM_ACAO'

export interface RoundMetrics {
  filters: { channel: Channel | null; abc_curve: string | null }
  items: number
  acceptance_rate: MetricValue
  estimated_review_hours: MetricValue
  in_competitive_band: MetricValue
  avg_gross_margin: MetricValue
  reversal_rate: MetricValue
  recommendation_distribution: Record<RecommendationType, number>
  price_index_by_curve: Record<'A' | 'B' | 'C', number | null>
  decisions_by_recommendation: Record<RecommendationType, Record<DecisionBucket, number>>
  rejection_reasons: Record<string, number>
  top_value_at_stake: {
    recommendation_id: string
    sku: string
    product_name: string
    channel: Channel
    recommendation: RecommendationType
    variation: number
    value_at_stake: number | null
    status: ItemStatus
  }[]
}

export interface HistoryItem extends Decision {
  sku: string
  product_name: string
  channel: Channel
}

export interface HistoryFilters {
  user_id?: string
  decision?: DecisionType
  channel?: Channel
  date_from?: string
  date_to?: string
  page?: number
  page_size?: number
}

export interface ImportResult {
  round_id: string
  round_date: string
  imported: number
}
