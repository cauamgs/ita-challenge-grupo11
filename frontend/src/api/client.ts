export class ApiError extends Error {
  status: number
  errors: unknown[]

  constructor(status: number, message: string, errors: unknown[] = []) {
    super(message)
    this.status = status
    this.errors = errors
  }
}

type Params = Record<string, string | number | boolean | undefined | null>

export function buildQuery(params: Params = {}): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, init)
  } catch {
    throw new ApiError(0, 'Não foi possível conectar ao servidor.')
  }
  if (!response.ok) {
    let message = `Erro ${response.status}`
    let errors: unknown[] = []
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') message = body.detail
      if (Array.isArray(body.errors)) errors = body.errors
    } catch {
      /* corpo não é JSON */
    }
    throw new ApiError(response.status, message, errors)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
