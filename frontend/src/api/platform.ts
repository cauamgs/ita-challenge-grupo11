/** Consultas e mutações das áreas de plataforma: dashboard, ERP, produtos e analistas. */
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ApiError, buildQuery, postJson, request } from './client'
import type {
  AnalystDetail,
  AnalystSummary,
  Dashboard,
  ErpStatus,
  Page,
  ProductDetail,
  ProductFilters,
  ProductListItem,
  ScheduleInput,
  SyncRun,
  SyncSchedule,
} from './types'

export const platformKeys = {
  dashboard: (roundId?: string) => ['dashboard', roundId ?? ''] as const,
  erpStatus: ['erp', 'status'] as const,
  erpSyncs: (page: number) => ['erp', 'syncs', page] as const,
  erpPreview: (input: ScheduleInput) => ['erp', 'preview', input] as const,
  products: (filters: ProductFilters) => ['products', 'list', filters] as const,
  product: (sku: string) => ['products', 'detail', sku] as const,
  categories: ['products', 'categories'] as const,
  analysts: ['analysts'] as const,
  analyst: (id: string) => ['analysts', id] as const,
}

export function useDashboard(roundId?: string) {
  return useQuery({
    queryKey: platformKeys.dashboard(roundId),
    queryFn: () => request<Dashboard>(`/dashboard${buildQuery({ round_id: roundId })}`),
    placeholderData: keepPreviousData,
  })
}

export function useErpStatus() {
  return useQuery({
    queryKey: platformKeys.erpStatus,
    queryFn: () => request<ErpStatus>('/erp/status'),
  })
}

export function useErpSyncs(page: number) {
  return useQuery({
    queryKey: platformKeys.erpSyncs(page),
    queryFn: () => request<Page<SyncRun>>(`/erp/syncs${buildQuery({ page, page_size: 10 })}`),
    placeholderData: keepPreviousData,
  })
}

export function useSchedulePreview(input: ScheduleInput, enabled: boolean) {
  return useQuery({
    queryKey: platformKeys.erpPreview(input),
    queryFn: () =>
      postJson<{ description: string; next_run_at: string }>('/erp/schedule/preview', input),
    enabled,
    retry: false,
  })
}

function invalidatePlatform(queryClient: ReturnType<typeof useQueryClient>) {
  for (const key of ['erp', 'dashboard', 'products', 'rounds', 'recommendations'])
    queryClient.invalidateQueries({ queryKey: [key] })
}

export function useSyncNow() {
  const queryClient = useQueryClient()
  return useMutation<SyncRun, ApiError, { userId?: string }>({
    mutationFn: ({ userId }) => postJson<SyncRun>('/erp/sync', { user_id: userId ?? null }),
    onSettled: () => invalidatePlatform(queryClient),
  })
}

export function useImportErpFile() {
  const queryClient = useQueryClient()
  return useMutation<SyncRun, ApiError, { file: File; userId?: string }>({
    mutationFn: ({ file, userId }) => {
      const body = new FormData()
      body.append('file', file)
      if (userId) body.append('user_id', userId)
      return request<SyncRun>('/erp/import', { method: 'POST', body })
    },
    onSettled: () => invalidatePlatform(queryClient),
  })
}

export function useSaveSchedule() {
  const queryClient = useQueryClient()
  return useMutation<SyncSchedule, ApiError, ScheduleInput>({
    mutationFn: (input) =>
      request<SyncSchedule>('/erp/schedule', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(input),
      }),
    onSettled: () => invalidatePlatform(queryClient),
  })
}

export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: platformKeys.products(filters),
    queryFn: () => request<Page<ProductListItem>>(`/products${buildQuery({ ...filters })}`),
    placeholderData: keepPreviousData,
  })
}

export function useCategories() {
  return useQuery({
    queryKey: platformKeys.categories,
    queryFn: () => request<string[]>('/products/categories'),
    staleTime: 5 * 60_000,
  })
}

export function useProduct(sku: string) {
  return useQuery({
    queryKey: platformKeys.product(sku),
    queryFn: () => request<ProductDetail>(`/products/${encodeURIComponent(sku)}`),
  })
}

export function useAnalysts() {
  return useQuery({
    queryKey: platformKeys.analysts,
    queryFn: () => request<AnalystSummary[]>('/analysts'),
  })
}

export function useAnalyst(id: string) {
  return useQuery({
    queryKey: platformKeys.analyst(id),
    queryFn: () => request<AnalystDetail>(`/analysts/${id}`),
  })
}
