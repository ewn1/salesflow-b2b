import { configureStore } from '@reduxjs/toolkit'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import reducer, {
  loadCurrentUser,
  login,
  register,
  sessionEnded,
  userLoaded,
} from './authSlice'
import { getAccessToken, getRefreshToken, saveTokens } from './tokenStorage'

const user = { id: 1, username: 'alice', email: 'alice@example.com' }

const fetchMock = vi.fn()

function makeStore() {
  return configureStore({ reducer: { auth: reducer } })
}

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
  vi.unstubAllEnvs()
  vi.unstubAllGlobals()
  localStorage.clear()
})

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

describe('loadCurrentUser', () => {
  it('moves from checking to authenticated with the user returned by the API', async () => {
    saveTokens({ access: 'access-1', refresh: 'refresh-1' })
    fetchMock.mockResolvedValueOnce(
      new Response(JSON.stringify(user), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    )
    const store = makeStore()

    await store.dispatch(loadCurrentUser())

    expect(store.getState().auth).toEqual({ status: 'authenticated', user })
  })

  it.each([
    [
      'the API rejects the token',
      () =>
        Promise.resolve(
          new Response(JSON.stringify({ detail: 'Invalid token' }), {
            status: 401,
            headers: { 'Content-Type': 'application/json' },
          }),
        ),
    ],
    [
      'the network fails',
      () => Promise.reject(new TypeError('Failed to fetch')),
    ],
  ])('goes from checking to anonymous when %s', async (_reason, answer) => {
    saveTokens({ access: 'access-1', refresh: 'refresh-1' })
    fetchMock.mockImplementation(answer)
    const store = makeStore()
    expect(store.getState().auth.status).toBe('checking')

    await store.dispatch(loadCurrentUser())

    expect(store.getState().auth).toEqual({ status: 'anonymous', user: null })
  })
})

describe('login', () => {
  it('stores the tokens and ends up authenticated with the user', async () => {
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({ access: 'access-1', refresh: 'refresh-1' }),
      )
      .mockResolvedValueOnce(jsonResponse(user))
    const store = makeStore()

    await store.dispatch(login({ username: 'alice', password: 'secret-pass' }))

    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      username: 'alice',
      password: 'secret-pass',
    })
    expect(getAccessToken()).toBe('access-1')
    expect(getRefreshToken()).toBe('refresh-1')
    expect(store.getState().auth).toEqual({ status: 'authenticated', user })
  })

  it('clears the stored tokens when the user cannot be loaded after the login', async () => {
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({ access: 'access-1', refresh: 'refresh-1' }),
      )
      .mockResolvedValueOnce(jsonResponse({ detail: 'Server error' }, 500))
    const store = makeStore()

    await store.dispatch(login({ username: 'alice', password: 'secret-pass' }))

    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
    expect(store.getState().auth).toEqual({ status: 'anonymous', user: null })
  })

  it.each([
    [
      'the API refuses the credentials',
      () =>
        Promise.resolve(
          jsonResponse({ detail: 'No active account found' }, 401),
        ),
      { status: 401, data: { detail: 'No active account found' } },
    ],
    [
      'the network fails',
      () => Promise.reject(new TypeError('Failed to fetch')),
      { status: null, data: null },
    ],
  ])(
    'rejects with a plain error value when %s',
    async (_reason, answer, expected) => {
      fetchMock.mockImplementation(answer)
      const store = makeStore()

      const result = await store.dispatch(
        login({ username: 'alice', password: 'wrong-pass' }),
      )

      expect(login.rejected.match(result)).toBe(true)
      expect(result.payload).toEqual(expected)
      expect(getAccessToken()).toBeNull()
      expect(store.getState().auth.status).toBe('anonymous')
    },
  )
})

describe('register', () => {
  const newAccount = {
    username: 'alice',
    email: 'alice@example.com',
    password: 'S3cure-pass-phrase!',
  }

  it('creates the account without opening a session', async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        { id: 1, username: 'alice', email: 'alice@example.com' },
        201,
      ),
    )
    const store = makeStore()

    const result = await store.dispatch(register(newAccount))

    expect(register.fulfilled.match(result)).toBe(true)
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual(newAccount)
    expect(getAccessToken()).toBeNull()
    expect(store.getState().auth).toEqual({ status: 'anonymous', user: null })
  })

  it('rejects with the field errors returned by the API', async () => {
    const fieldErrors = { email: ['A user with this email already exists.'] }
    fetchMock.mockResolvedValueOnce(jsonResponse(fieldErrors, 400))
    const store = makeStore()

    const result = await store.dispatch(register(newAccount))

    expect(register.rejected.match(result)).toBe(true)
    expect(result.payload).toEqual({ status: 400, data: fieldErrors })
  })
})
