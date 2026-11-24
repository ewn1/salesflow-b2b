import '@fontsource-variable/inter/wght.css'
import '@fontsource-variable/roboto-mono/wght.css'
import './index.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { routes } from './routes'
import { Provider } from 'react-redux'
import { connectSessionExpiry, createAppStore, restoreSession } from './store'

const store = createAppStore()
// Order matters: the expiry hook must exist before the first request,
// because restoring the session can itself end it.
connectSessionExpiry(store)
void restoreSession(store)

const router = createBrowserRouter(routes)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Provider store={store}>
      <RouterProvider router={router} />
    </Provider>
  </StrictMode>,
)
