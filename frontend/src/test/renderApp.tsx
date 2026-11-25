import { render } from '@testing-library/react'
import { Provider } from 'react-redux'
import { createMemoryRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { routes } from '../routes'
import { createAppStore } from '../store'

// Renders the real app (real routes, fresh store) starting at `path`.
export function renderApp(path: string) {
  const store = createAppStore()
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(
    <Provider store={store}>
      <RouterProvider router={router} />
    </Provider>,
  )
  return { store, router }
}
