import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../components/AppShell'
import { ToastProvider } from '../components/Toast'
import { AnalystDetailPage } from '../pages/AnalystDetailPage'
import { AnalystsPage } from '../pages/AnalystsPage'
import { DashboardPage } from '../pages/DashboardPage'
import { ErpPage } from '../pages/ErpPage'
import { HistoryPage } from '../pages/HistoryPage'
import { ProductDetailPage } from '../pages/ProductDetailPage'
import { ProductsPage } from '../pages/ProductsPage'
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
                <Route index element={<Navigate to="/inicio" replace />} />
                <Route path="/inicio" element={<DashboardPage />} />
                <Route path="/recomendacoes" element={<RecommendationsPage />} />
                <Route path="/metricas" element={<MetricsPage />} />
                <Route path="/produtos" element={<ProductsPage />} />
                <Route path="/produtos/:sku" element={<ProductDetailPage />} />
                <Route path="/analistas" element={<AnalystsPage />} />
                <Route path="/analistas/:id" element={<AnalystDetailPage />} />
                <Route path="/historico" element={<HistoryPage />} />
                <Route path="/erp" element={<ErpPage />} />
                <Route path="*" element={<Navigate to="/inicio" replace />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </SessionProvider>
    </QueryClientProvider>
  )
}
