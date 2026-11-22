import {
  createAsyncThunk,
  createSlice,
  type PayloadAction,
} from '@reduxjs/toolkit'
import { ApiError, request } from '../api/client'
import { clearTokens, getAccessToken, saveTokens } from './tokenStorage'

export type User = {
  id: number
  username: string
  email: string
}

export type AuthStatus = 'checking' | 'anonymous' | 'authenticated'

export type AuthState = {
  status: AuthStatus
  user: User | null
}

// A stored token does not prove the session is valid: the API still has to
// confirm it, so the app starts in "checking" until the user is loaded.
function getInitialState(): AuthState {
  return {
    status: getAccessToken() ? 'checking' : 'anonymous',
    user: null,
  }
}

export const loadCurrentUser = createAsyncThunk('auth/loadCurrentUser', () =>
  request<User>('/auth/me/'),
)

type Credentials = { username: string; password: string }
type TokenPair = { access: string; refresh: string }

export type AuthError = { status: number | null; data: unknown }

// Thunks reject with plain data: Redux actions must stay serializable, and
// the form needs the HTTP status to pick the right message.
function toAuthError(error: unknown): AuthError {
  return error instanceof ApiError
    ? { status: error.status, data: error.data }
    : { status: null, data: null }
}

export const login = createAsyncThunk<
  User,
  Credentials,
  { rejectValue: AuthError }
>('auth/login', async (credentials, { rejectWithValue }) => {
  let tokens: TokenPair
  try {
    tokens = await request<TokenPair>('/auth/token/', {
      method: 'POST',
      body: credentials,
      auth: false,
    })
  } catch (error) {
    return rejectWithValue(toAuthError(error))
  }

  saveTokens(tokens)
  try {
    return await request<User>('/auth/me/')
  } catch (error) {
    // Never keep a half-open session: tokens without a known user.
    clearTokens()
    return rejectWithValue(toAuthError(error))
  }
})

const authSlice = createSlice({
  name: 'auth',
  initialState: getInitialState,
  reducers: {
    userLoaded(state, action: PayloadAction<User>) {
      state.status = 'authenticated'
      state.user = action.payload
    },
    sessionEnded(state) {
      state.status = 'anonymous'
      state.user = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loadCurrentUser.fulfilled, (state, action) => {
        state.status = 'authenticated'
        state.user = action.payload
      })
      .addCase(loadCurrentUser.rejected, (state) => {
        state.status = 'anonymous'
        state.user = null
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = 'authenticated'
        state.user = action.payload
      })
  },
})

export const { userLoaded, sessionEnded } = authSlice.actions
export default authSlice.reducer
