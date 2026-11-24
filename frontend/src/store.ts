import { configureStore } from '@reduxjs/toolkit'
import { setSessionExpiredHandler } from './api/client'
import authReducer, { sessionEnded } from './auth/authSlice'

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
