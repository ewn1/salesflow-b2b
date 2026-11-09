import {
  createAsyncThunk,
  createSlice,
  type PayloadAction,
} from '@reduxjs/toolkit'
import { request } from '../api/client'
import { getAccessToken } from './tokenStorage'

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
  },
})

export const { userLoaded, sessionEnded } = authSlice.actions
export default authSlice.reducer
