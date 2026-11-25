import { afterEach, beforeEach, vi } from 'vitest'

export function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

// Call once per test file: it registers the hooks that stub the API address
// and `fetch`, and cleans everything (including stored tokens) between tests.
export function setupFetchMock() {
  const fetchMock = vi.fn()

  beforeEach(() => {
    vi.stubEnv('VITE_API_URL', 'http://api.test')
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    fetchMock.mockReset()
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
    localStorage.clear()
  })

  return fetchMock
}
