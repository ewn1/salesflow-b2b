import { configureStore } from '@reduxjs/toolkit'
import { setSessionExpiredHandler } from './api/client'
import authReducer, { loadCurrentUser, sessionEnded } from './auth/authSlice'

export function createAppStore() {
  return configureStore({ reducer: { auth: authReducer } })
}

export type AppStore = ReturnType<typeof createAppStore>
export type RootState = ReturnType<AppStore['getState']>
export type AppDispatch = AppStore['dispatch']

// The API client knows nothing about Redux: it only announces that the
// session is over. This is where that announcement reaches the store.
export function connectSessionExpiry(store: AppStore) {
  setSessionExpiredHandler(() => {
    store.dispatch(sessionEnded())
  })
}

// A stored token only means "maybe logged in": the API still has to say who
// the user is. Without a token the status is already "anonymous" and no
// request is made.
export async function restoreSession(store: AppStore) {
  if (store.getState().auth.status === 'checking') {
    await store.dispatch(loadCurrentUser())
  }
}
