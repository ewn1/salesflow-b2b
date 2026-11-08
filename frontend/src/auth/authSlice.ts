import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

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

const initialState: AuthState = { status: 'anonymous', user: null }

const authSlice = createSlice({
  name: 'auth',
  initialState,
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
})

export const { userLoaded, sessionEnded } = authSlice.actions
export default authSlice.reducer
