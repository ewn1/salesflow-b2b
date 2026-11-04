import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError, request } from './client'
import { saveTokens } from '../auth/tokenStorage'

const fetchMock = vi.fn()

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('request', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.stubEnv('VITE_API_URL', 'http://api.test/api')
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    localStorage.clear()
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
})
