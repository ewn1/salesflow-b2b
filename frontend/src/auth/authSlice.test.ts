import { describe, expect, it } from 'vitest'
import reducer, { sessionEnded, userLoaded } from './authSlice'

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
