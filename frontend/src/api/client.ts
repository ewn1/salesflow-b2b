// Thin wrapper around fetch for the Sales Flow API: base URL, JSON, the
// Authorization header and one token refresh when the API answers 401.

import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  saveTokens,
  type Tokens,
} from '../auth/tokenStorage'

export class ApiError extends Error {
  readonly status: number
  readonly data: unknown

  constructor(status: number, data: unknown) {
    super(`API request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

type RequestOptions = {
  method?: string
  body?: unknown
  // Set to false for public endpoints (login, register, refresh)
  auth?: boolean
}

let sessionExpiredHandler: (() => void) | null = null

// The app registers what happens when the session ends (for example, log out
// and go to the login page), so this module does not depend on the store.
export function setSessionExpiredHandler(handler: (() => void) | null): void {
  sessionExpiredHandler = handler
}

function getBaseUrl(): string {
  const baseUrl = import.meta.env.VITE_API_URL
  if (!baseUrl) {
    throw new Error('VITE_API_URL is not set. Copy .env.example to .env.')
  }
  return baseUrl.replace(/\/+$/, '')
}

// Read the body as text first: an empty body (204) or a non-JSON body (an HTML
// error page from a proxy) must not crash the client.
async function readBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (text === '') {
    return undefined
  }
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

// A single attempt: no refresh, no retry.
async function send<T>(path: string, options: RequestOptions): Promise<T> {
  const { auth = true } = options
  const url = `${getBaseUrl()}${path}`
  const headers = new Headers()
  const init: RequestInit = { method: options.method ?? 'GET', headers }

  if (auth) {
    const token = getAccessToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }

  if (options.body !== undefined) {
    headers.set('Content-Type', 'application/json')
    init.body = JSON.stringify(options.body)
  }

  const response = await fetch(url, init)
  const data = await readBody(response)

  if (!response.ok) {
    throw new ApiError(response.status, data)
  }

  // The cast is a promise from the caller, not a runtime check.
  return data as T
}

function isUnauthorized(error: unknown): boolean {
  return error instanceof ApiError && error.status === 401
}

function endSession(): void {
  clearTokens()
  sessionExpiredHandler?.()
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken()
  if (!refresh) {
    return false
  }
  try {
    const tokens = await send<Tokens>('/auth/token/refresh/', {
      method: 'POST',
      body: { refresh },
      auth: false,
    })
    saveTokens(tokens)
    return true
  } catch {
    return false
  }
}

// Requests that fail with 401 at the same time share one refresh call.
let refreshInFlight: Promise<boolean> | null = null

function refreshOnce(): Promise<boolean> {
  refreshInFlight ??= refreshAccessToken().finally(() => {
    refreshInFlight = null
  })
  return refreshInFlight
}

export async function request<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { auth = true } = options
  const tokenUsed = auth ? getAccessToken() : null

  try {
    return await send<T>(path, options)
  } catch (error) {
    if (!auth || !isUnauthorized(error)) {
      throw error
    }
    // Another request may have renewed the token while this one was in
    // flight. If so, just repeat the call with the new token.
    const currentToken = getAccessToken()
    const alreadyRenewed = currentToken !== null && currentToken !== tokenUsed
    if (!alreadyRenewed && !(await refreshOnce())) {
      endSession()
      throw error
    }
  }

  // The access token is valid again: repeat the original call, once.
  try {
    return await send<T>(path, options)
  } catch (error) {
    if (isUnauthorized(error)) {
      endSession()
    }
    throw error
  }
}
