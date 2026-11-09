import { afterEach, describe, expect, it } from 'vitest'
import reducer, { sessionEnded, userLoaded } from './authSlice'
import { saveTokens } from './tokenStorage'

const user = { id: 1, username: 'alice', email: 'alice@example.com' }

describe('authSlice reducers', () => {
  it('userLoaded marks the session as authenticated and stores the user', () => {
    const state = reducer({ status: 'checking', user: null }, userLoaded(user))

    expect(state).toEqual({ status: 'authenticated', user })
  })

  it('sessionEnded goes back to anonymous and drops the user', () => {
    const state = reducer({ status: 'authenticated', user }, sessionEnded())

    expect(state).toEqual({ status: 'anonymous', user: null })
  })
})

describe('authSlice initial state', () => {
  afterEach(() => {
    localStorage.clear()
  })

  it('starts anonymous when there is no stored token', () => {
    const state = reducer(undefined, { type: 'init' })

    expect(state).toEqual({ status: 'anonymous', user: null })
  })

  it('starts checking when a token is stored, until the user is loaded', () => {
    saveTokens({ access: 'access-1', refresh: 'refresh-1' })

    const state = reducer(undefined, { type: 'init' })

    expect(state).toEqual({ status: 'checking', user: null })
  })
})
