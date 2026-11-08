import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  getAccessToken,
  getRefreshToken,
  saveTokens,
} from '../auth/tokenStorage'
import { ApiError, request, setSessionExpiredHandler } from './client'

const fetchMock = vi.fn()

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function fakeServer(validAccess: string, refreshResponse: () => Response) {
  fetchMock.mockImplementation((url: string, init: RequestInit) => {
    if (url.endsWith('/auth/token/refresh/')) {
      return Promise.resolve(refreshResponse())
    }
    const authorization = new Headers(init.headers).get('Authorization')
    return Promise.resolve(
      authorization === `Bearer ${validAccess}`
        ? jsonResponse({ ok: true })
        : jsonResponse({ detail: 'Token is expired' }, 401),
    )
  })
}

function refreshCalls() {
  return fetchMock.mock.calls.filter(([url]) =>
    String(url).endsWith('/auth/token/refresh/'),
  )
}

describe('request', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubEnv('VITE_API_URL', 'http://api.test/api')
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    localStorage.clear()
    setSessionExpiredHandler(null)
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    fetchMock.mockReset()
  })

  it('calls the API base URL joined with the path', async () => {
    fetchMock.mockResolvedValue(jsonResponse({}))

    await request('/dashboard/summary/')

    expect(fetchMock).toHaveBeenCalledOnce()
    expect(fetchMock.mock.calls[0][0]).toBe(
      'http://api.test/api/dashboard/summary/',
    )
  })

  it('returns the parsed JSON body', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ revenue: '1500.50' }))

    const data = await request<{ revenue: string }>('/dashboard/summary/')

    expect(data).toEqual({ revenue: '1500.50' })
  })

  it('sends an object body as JSON', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: 1 }, 201))

    await request('/clients/', { method: 'POST', body: { name: 'Acme' } })

    const init = fetchMock.mock.calls[0][1]
    expect(init.method).toBe('POST')
    expect(init.body).toBe('{"name":"Acme"}')
    expect(new Headers(init.headers).get('Content-Type')).toBe(
      'application/json',
    )
  })

  it('returns undefined when the API answers 204 No Content', async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    const data = await request('/clients/1/', { method: 'DELETE' })

    expect(data).toBeUndefined()
  })

  it('throws an ApiError with status and body on an error response', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Not found.' }, 404))

    const error = await request('/clients/99/').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 404, data: { detail: 'Not found.' } })
  })

  it('throws an ApiError even when the error body is not JSON', async () => {
    fetchMock.mockResolvedValue(new Response('Bad gateway', { status: 502 }))

    const error = await request('/clients/').catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 502, data: null })
  })

  it('fails with a clear message when VITE_API_URL is not set', async () => {
    vi.stubEnv('VITE_API_URL', '')

    await expect(request('/clients/')).rejects.toThrow('VITE_API_URL')
  })

  describe('authentication', () => {
    it('sends the access token as a Bearer header', async () => {
      saveTokens({ access: 'access-1', refresh: 'refresh-1' })
      fetchMock.mockResolvedValue(jsonResponse({}))

      await request('/dashboard/summary/')

      const init = fetchMock.mock.calls[0][1]
      expect(new Headers(init.headers).get('Authorization')).toBe(
        'Bearer access-1',
      )
    })

    it('sends no Authorization header when there is no token', async () => {
      fetchMock.mockResolvedValue(jsonResponse({}))

      await request('/dashboard/summary/')

      const init = fetchMock.mock.calls[0][1]
      expect(new Headers(init.headers).get('Authorization')).toBeNull()
    })

    it('sends no Authorization header when auth is disabled', async () => {
      saveTokens({ access: 'access-1', refresh: 'refresh-1' })
      fetchMock.mockResolvedValue(jsonResponse({ access: 'a', refresh: 'r' }))

      await request('/auth/token/', {
        method: 'POST',
        body: { username: 'demo', password: 'secret' },
        auth: false,
      })

      const init = fetchMock.mock.calls[0][1]
      expect(new Headers(init.headers).get('Authorization')).toBeNull()
    })
  })

  describe('token refresh', () => {
    const refreshOk = () => jsonResponse({ access: 'access-2' })

    beforeEach(() => {
      saveTokens({ access: 'access-1', refresh: 'refresh-1' })
    })

    it('refreshes the access token and retries the request once', async () => {
      fakeServer('access-2', refreshOk)

      const data = await request('/dashboard/summary/')

      expect(data).toEqual({ ok: true })
      expect(getAccessToken()).toBe('access-2')
      expect(refreshCalls()).toHaveLength(1)
      const [, init] = refreshCalls()[0]
      expect(init.method).toBe('POST')
      expect(init.body).toBe('{"refresh":"refresh-1"}')
      expect(new Headers(init.headers).get('Authorization')).toBeNull()
    })

    it('stores a rotated refresh token when the API returns one', async () => {
      fakeServer('access-2', () =>
        jsonResponse({ access: 'access-2', refresh: 'refresh-2' }),
      )

      await request('/dashboard/summary/')

      expect(getRefreshToken()).toBe('refresh-2')
    })

    it('shares a single refresh between concurrent requests', async () => {
      fakeServer('access-2', refreshOk)

      const results = await Promise.all([
        request('/clients/'),
        request('/orders/'),
      ])

      expect(results).toEqual([{ ok: true }, { ok: true }])
      expect(refreshCalls()).toHaveLength(1)
    })

    it('does not refresh when auth is disabled', async () => {
      fakeServer('never', refreshOk)

      const error = await request('/auth/token/', {
        method: 'POST',
        body: { username: 'demo', password: 'wrong' },
        auth: false,
      }).catch((e: unknown) => e)

      expect(error).toMatchObject({ status: 401 })
      expect(fetchMock).toHaveBeenCalledOnce()
      expect(getAccessToken()).toBe('access-1')
    })

    it('retries without refreshing when another request already renewed the token', async () => {
      fakeServer('access-2', refreshOk)
      // The first call (sent with access-1) stays pending until we answer it.
      let answerLate: (response: Response) => void = () => {}
      fetchMock.mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            answerLate = resolve
          }),
      )

      const late = request('/orders/')
      // Meanwhile, another request finished renewing the token.
      saveTokens({ access: 'access-2' })
      answerLate(jsonResponse({ detail: 'Token is expired' }, 401))

      await expect(late).resolves.toEqual({ ok: true })
      expect(refreshCalls()).toHaveLength(0)
    })

    it('clears the tokens and notifies the app when the refresh fails', async () => {
      const onExpired = vi.fn()
      setSessionExpiredHandler(onExpired)
      fakeServer('access-2', () =>
        jsonResponse({ detail: 'Token is invalid' }, 401),
      )

      const error = await request('/dashboard/summary/').catch(
        (e: unknown) => e,
      )

      expect(error).toBeInstanceOf(ApiError)
      expect(error).toMatchObject({
        status: 401,
        data: { detail: 'Token is expired' },
      })
      expect(getAccessToken()).toBeNull()
      expect(getRefreshToken()).toBeNull()
      expect(onExpired).toHaveBeenCalledOnce()
    })

    it('treats a 401 without a refresh token as an expired session', async () => {
      const onExpired = vi.fn()
      setSessionExpiredHandler(onExpired)
      localStorage.clear()
      saveTokens({ access: 'access-1' })
      fakeServer('access-2', refreshOk)

      const error = await request('/dashboard/summary/').catch(
        (e: unknown) => e,
      )

      expect(error).toMatchObject({ status: 401 })
      expect(refreshCalls()).toHaveLength(0)
      expect(getAccessToken()).toBeNull()
      expect(onExpired).toHaveBeenCalledOnce()
    })

    it('does not retry more than once', async () => {
      fakeServer('never', refreshOk)

      const error = await request('/dashboard/summary/').catch(
        (e: unknown) => e,
      )

      expect(error).toMatchObject({ status: 401 })
      expect(refreshCalls()).toHaveLength(1)
      expect(fetchMock).toHaveBeenCalledTimes(3)
    })
  })
})
