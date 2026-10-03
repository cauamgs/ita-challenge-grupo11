import { NavLink, Outlet, useLocation } from 'react-router-dom'
import logo from '../assets/logo_popular_pet.png'
import { useSession } from '../app/session'
import { formatDate } from '../lib/format'
import { ROLE_LABEL } from '../lib/labels'

const TABS = [
  { to: '/inicio', label: 'Início', title: 'Painel da precificação' },
  { to: '/recomendacoes', label: 'Recomendações', title: 'Recomendações de preço' },
  { to: '/metricas', label: 'Métricas', title: 'Métricas da carteira' },
  { to: '/produtos', label: 'Produtos', title: 'Produtos e histórico de preços' },
  { to: '/analistas', label: 'Analistas', title: 'Histórico de análises' },
  { to: '/historico', label: 'Histórico', title: 'Histórico de decisões' },
  { to: '/erp', label: 'Integração ERP', title: 'Integração com o ERP' },
]

const headerSelect =
  'h-8 rounded border border-white/30 bg-white/15 px-2 text-[13px] text-white [&>option]:text-ink'

export function AppShell() {
  const { pathname } = useLocation()
  const current = TABS.find((t) => pathname.startsWith(t.to)) ?? TABS[0]
  const session = useSession()

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 bg-brand-purple text-white">
        <div className="mx-auto flex h-14 max-w-[1440px] items-center gap-3 px-4">
          <img src={logo} alt="Popular Pet" className="h-8 w-8 rounded-md" />
          <h1 className="truncate text-base font-bold">{current.title}</h1>
          <div className="ml-auto flex items-center gap-2">
            <label className="flex items-center gap-1.5 text-xs text-white/80">
              Rodada
              <select
                className={headerSelect}
                value={session.currentRound?.id ?? ''}
                onChange={(e) => session.setCurrentRoundId(e.target.value)}
                disabled={!session.rounds.length}
              >
                {!session.rounds.length && <option value="">Nenhuma rodada</option>}
                {session.rounds.map((r) => (
                  <option key={r.id} value={r.id}>
                    {formatDate(r.round_date)}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center gap-1.5 text-xs text-white/80">
              Analista
              <select
                className={headerSelect}
                value={session.currentUser?.id ?? ''}
                onChange={(e) => session.setCurrentUserId(e.target.value)}
                disabled={!session.users.length}
              >
                {session.users.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.name} ({ROLE_LABEL[u.role]})
                  </option>
                ))}
              </select>
            </label>
          </div>
        </div>
      </header>
      <nav className="border-b border-line bg-surface" aria-label="Navegação principal">
        <div className="mx-auto flex max-w-[1440px] gap-5 overflow-x-auto px-4">
          {TABS.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              className={({ isActive }) =>
                `whitespace-nowrap border-b-[3px] py-3 text-sm font-semibold ${
                  isActive
                    ? 'border-brand-lime text-brand-purple'
                    : 'border-transparent text-ink-muted hover:text-brand-purple'
                }`
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </div>
      </nav>
      <main className="mx-auto w-full max-w-[1440px] flex-1 px-4 py-4">
        <Outlet />
      </main>
      <footer className="h-1 bg-brand-lime" />
    </div>
  )
}
