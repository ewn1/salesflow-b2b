// Thin wrapper around fetch for the Sales Flow API.
// Auth headers and token refresh are added in later steps.

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

export async function request<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const url = `${getBaseUrl()}${path}`
  const headers = new Headers()
  const init: RequestInit = { method: options.method ?? 'GET', headers }

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
