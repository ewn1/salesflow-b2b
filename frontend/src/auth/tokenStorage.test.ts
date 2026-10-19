import { beforeEach, describe, expect, it } from 'vitest'
import {
  clearTokens,
  getAccessToken,
  getRefreshToken,
  saveTokens,
} from './tokenStorage'

describe('tokenStorage', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('returns null when nothing was saved', () => {
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })

  it('returns the saved tokens', () => {
    saveTokens({ access: 'access-1', refresh: 'refresh-1' })

    expect(getAccessToken()).toBe('access-1')
    expect(getRefreshToken()).toBe('refresh-1')
  })

  it('keeps the refresh token when only a new access token is saved', () => {
    saveTokens({ access: 'access-1', refresh: 'refresh-1' })
    saveTokens({ access: 'access-2' })

    expect(getAccessToken()).toBe('access-2')
    expect(getRefreshToken()).toBe('refresh-1')
  })

  it('removes both tokens on clear', () => {
    saveTokens({ access: 'access-1', refresh: 'refresh-1' })
    clearTokens()

    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })
})
