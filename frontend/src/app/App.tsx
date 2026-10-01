import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { ToastProvider } from '../components/Toast'
import { HistoryPage } from '../pages/HistoryPage'
import { MetricsPage } from '../pages/MetricsPage'
import { RecommendationsPage } from '../pages/RecommendationsPage'
import { SessionProvider } from './session'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false } },
})

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <SessionProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>
              <Route element={<AppShell />}>
                <Route index element={<Navigate to="/recomendacoes" replace />} />
                <Route path="/recomendacoes" element={<RecommendationsPage />} />
                <Route path="/metricas" element={<MetricsPage />} />
                <Route path="/historico" element={<HistoryPage />} />
                <Route path="*" element={<Navigate to="/recomendacoes" replace />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </SessionProvider>
    </QueryClientProvider>
  )
}
