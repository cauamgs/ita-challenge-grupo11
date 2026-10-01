import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import { useRounds, useUsers } from '../api/queries'
import type { Round, User } from '../api/types'

/**
 * Sessão da v1: o analista escolhe o nome num seletor (sem login) e a rodada ativa.
 * Para trocar por login depois, basta mudar a origem de `currentUser` aqui.
 */
interface SessionValue {
  users: User[]
  currentUser: User | null
  setCurrentUserId: (id: string) => void
  rounds: Round[]
  currentRound: Round | null
  setCurrentRoundId: (id: string) => void
  isLoading: boolean
}

const SessionContext = createContext<SessionValue | null>(null)
const USER_KEY = 'popularpet.analystId'

function readStoredUser(): string | null {
  try {
    return localStorage.getItem(USER_KEY)
  } catch {
    return null
  }
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const usersQuery = useUsers()
  const roundsQuery = useRounds()
  const [userId, setUserId] = useState<string | null>(readStoredUser)
  const [roundId, setRoundId] = useState<string | null>(null)

  const value = useMemo<SessionValue>(() => {
    const users = usersQuery.data ?? []
    const rounds = roundsQuery.data ?? []
    return {
      users,
      currentUser: users.find((u) => u.id === userId) ?? users[0] ?? null,
      setCurrentUserId: (id: string) => {
        setUserId(id)
        try {
          localStorage.setItem(USER_KEY, id)
        } catch {
          /* armazenamento indisponível: fica só na sessão */
        }
      },
      rounds,
      // Rodada mais recente por padrão (a API devolve em ordem decrescente de data)
      currentRound: rounds.find((r) => r.id === roundId) ?? rounds[0] ?? null,
      setCurrentRoundId: setRoundId,
      isLoading: usersQuery.isLoading || roundsQuery.isLoading,
    }
  }, [
    usersQuery.data,
    usersQuery.isLoading,
    roundsQuery.data,
    roundsQuery.isLoading,
    userId,
    roundId,
  ])

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

// eslint-disable-next-line react-refresh/only-export-components
export function useSession(): SessionValue {
  const ctx = useContext(SessionContext)
  if (!ctx) throw new Error('useSession fora do SessionProvider')
  return ctx
}
