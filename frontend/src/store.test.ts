import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { request, setSessionExpiredHandler } from './api/client'
import { loadCurrentUser } from './auth/authSlice'
import { getAccessToken, saveTokens } from './auth/tokenStorage'
import { connectSessionExpiry, createAppStore } from './store'

const user = { id: 1, username: 'alice', email: 'alice@example.com' }
const fetchMock = vi.fn()

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

beforeEach(() => {
  vi.stubEnv('VITE_API_URL', 'http://api.test')
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  setSessionExpiredHandler(null)
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  localStorage.clear()
})

describe('createAppStore', () => {
  it('starts anonymous when there is no stored token', () => {
    const store = createAppStore()

    expect(store.getState().auth.status).toBe('anonymous')
  })

  it('starts checking when a token is stored', () => {
    saveTokens({ access: 'access-1', refresh: 'refresh-1' })

    const store = createAppStore()

    expect(store.getState().auth.status).toBe('checking')
  })
})

describe('connectSessionExpiry', () => {
  it('sends the store back to anonymous when the API client reports an expired session', async () => {
    saveTokens({ access: 'access-1', refresh: 'refresh-1' })
    fetchMock.mockResolvedValueOnce(jsonResponse(user))
    fetchMock.mockImplementation(() =>
      Promise.resolve(jsonResponse({ detail: 'Token expired' }, 401)),
    )
    const store = createAppStore()
    connectSessionExpiry(store)
    await store.dispatch(loadCurrentUser())
    expect(store.getState().auth.status).toBe('authenticated')

    await request('/clients/').catch(() => undefined)

    expect(store.getState().auth).toEqual({ status: 'anonymous', user: null })
    expect(getAccessToken()).toBeNull()
  })
})
