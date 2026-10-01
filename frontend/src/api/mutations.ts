import { useMutation, useQueryClient, type QueryKey } from '@tanstack/react-query'
import { ApiError, postJson, request } from './client'
import type {
  DecisionCreated,
  DecisionInput,
  DecisionType,
  ImportResult,
  ItemStatus,
  Page,
  RecommendationItem,
} from './types'

const STATUS_BY_DECISION: Record<DecisionType, ItemStatus> = {
  APROVAR: 'APROVADA',
  EDITAR: 'EDITADA',
  REJEITAR: 'REJEITADA',
  ADIAR: 'ADIADA',
}

/** Registra uma decisão; atualiza a linha da lista de forma otimista e revalida o resto. */
export function useCreateDecision(recommendationId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: DecisionInput) =>
      postJson<DecisionCreated>(`/recommendations/${recommendationId}/decisions`, input),
    onMutate: async (input) => {
      const filter = { queryKey: ['rounds'] as QueryKey, predicate: isListQuery }
      await queryClient.cancelQueries(filter)
      const previous = queryClient.getQueriesData<Page<RecommendationItem>>(filter)
      queryClient.setQueriesData<Page<RecommendationItem>>(filter, (page) =>
        page
          ? {
              ...page,
              items: page.items.map((item) =>
                item.id === recommendationId
                  ? { ...item, status: STATUS_BY_DECISION[input.decision] }
                  : item,
              ),
            }
          : page,
      )
      return { previous }
    },
    onError: (_err, _input, context) => {
      context?.previous.forEach(([key, data]) => queryClient.setQueryData(key, data))
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['rounds'] })
      queryClient.invalidateQueries({ queryKey: ['recommendations'] })
      queryClient.invalidateQueries({ queryKey: ['decisions'] })
    },
  })
}

function isListQuery(query: { queryKey: QueryKey }): boolean {
  return query.queryKey[2] === 'recommendations'
}

/** Importa uma rodada (CSV) e revalida a lista de rodadas. */
export function useImportRound() {
  const queryClient = useQueryClient()
  return useMutation<ImportResult, ApiError, { file: File; replace: boolean; userId?: string }>({
    mutationFn: ({ file, replace, userId }) => {
      const body = new FormData()
      body.append('file', file)
      if (userId) body.append('user_id', userId)
      return request<ImportResult>(`/rounds/import${replace ? '?replace=true' : ''}`, {
        method: 'POST',
        body,
      })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['rounds'] }),
  })
}
