// Tokens live in localStorage by design (see "Auth: move the refresh token to
// an HttpOnly cookie" in docs/BACKLOG.md). Keep every read and write of them
// in this module so that changing the storage later touches a single file.

const ACCESS_KEY = 'salesflow.access'
const REFRESH_KEY = 'salesflow.refresh'

type Tokens = {
  access: string
  refresh?: string
}

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_KEY)
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_KEY)
}

export function saveTokens({ access, refresh }: Tokens): void {
  localStorage.setItem(ACCESS_KEY, access)
  if (refresh !== undefined) {
    localStorage.setItem(REFRESH_KEY, refresh)
  }
}

export function clearTokens(): void {
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
}
