import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { buildQuery, request } from './client'
import type {
  HistoryFilters,
  HistoryItem,
  Page,
  RecommendationDetail,
  RecommendationFilters,
  RecommendationItem,
  Round,
  RoundMetrics,
  RoundSummary,
  User,
} from './types'

export const queryKeys = {
  users: ['users'] as const,
  rounds: ['rounds'] as const,
  summary: (roundId: string) => ['rounds', roundId, 'summary'] as const,
  recommendations: (roundId: string, filters: RecommendationFilters) =>
    ['rounds', roundId, 'recommendations', filters] as const,
  recommendation: (id: string) => ['recommendations', id] as const,
  decisions: (filters: HistoryFilters) => ['decisions', filters] as const,
  metrics: (roundId: string, channel?: string, curve?: string) =>
    ['rounds', roundId, 'metrics', channel ?? '', curve ?? ''] as const,
}

export function useUsers() {
  return useQuery({ queryKey: queryKeys.users, queryFn: () => request<User[]>('/users') })
}

export function useRounds() {
  return useQuery({ queryKey: queryKeys.rounds, queryFn: () => request<Round[]>('/rounds') })
}

export function useRoundSummary(roundId: string | undefined) {
  return useQuery({
    queryKey: queryKeys.summary(roundId ?? ''),
    queryFn: () => request<RoundSummary>(`/rounds/${roundId}/summary`),
    enabled: !!roundId,
  })
}

export function useRecommendations(roundId: string | undefined, filters: RecommendationFilters) {
  return useQuery({
    queryKey: queryKeys.recommendations(roundId ?? '', filters),
    queryFn: () =>
      request<Page<RecommendationItem>>(
        `/rounds/${roundId}/recommendations${buildQuery({ ...filters })}`,
      ),
    enabled: !!roundId,
    placeholderData: keepPreviousData,
  })
}

export function useRecommendation(id: string | null) {
  return useQuery({
    queryKey: queryKeys.recommendation(id ?? ''),
    queryFn: () => request<RecommendationDetail>(`/recommendations/${id}`),
    enabled: !!id,
  })
}

export function useRoundMetrics(roundId: string | undefined, channel?: string, abcCurve?: string) {
  return useQuery({
    queryKey: queryKeys.metrics(roundId ?? '', channel, abcCurve),
    queryFn: () =>
      request<RoundMetrics>(
        `/rounds/${roundId}/metrics${buildQuery({ channel, abc_curve: abcCurve })}`,
      ),
    enabled: !!roundId,
    placeholderData: keepPreviousData,
  })
}

export function useDecisionHistory(filters: HistoryFilters) {
  return useQuery({
    queryKey: queryKeys.decisions(filters),
    queryFn: () => request<Page<HistoryItem>>(`/decisions${buildQuery({ ...filters })}`),
    placeholderData: keepPreviousData,
  })
}
