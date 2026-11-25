import { act, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { saveTokens } from './auth/tokenStorage'
import { restoreSession, type AppStore } from './store'
import { jsonResponse, setupFetchMock } from './test/http'
import { renderApp } from './test/renderApp'

const alice = { id: 1, username: 'alice', email: 'alice@example.com' }

// The store notifies React outside user events, so the restoration runs
// inside act() to keep the test environment in sync with the screen.
async function restore(store: AppStore) {
  await act(() => restoreSession(store))
}

function storeSession() {
  saveTokens({ access: 'access-1', refresh: 'refresh-1' })
}

describe('routes', () => {
  const fetchMock = setupFetchMock()

  it.each([
    ['/login', 'Entrar'],
    ['/register', 'Criar conta'],
  ])('renders the public page for %s', (path, title) => {
    renderApp(path)

    expect(screen.getByRole('heading', { name: title })).toBeInTheDocument()
  })

  it('renders a not found page for unknown paths', () => {
    renderApp('/does-not-exist')

    expect(
      screen.getByRole('heading', { name: 'Página não encontrada' }),
    ).toBeInTheDocument()
  })

  it('keeps the product name visible on every page', () => {
    renderApp('/login')

    expect(
      screen.getByRole('heading', { level: 1, name: 'Sales Flow B2B' }),
    ).toBeInTheDocument()
  })

  describe('route guards', () => {
    it('sends an anonymous visitor from the dashboard to the login page', async () => {
      renderApp('/')

      expect(
        await screen.findByRole('heading', { name: 'Entrar' }),
      ).toBeInTheDocument()
      expect(
        screen.queryByRole('heading', { name: 'Painel' }),
      ).not.toBeInTheDocument()
    })

    it('shows a loading message, not the login page, while a stored session is checked', () => {
      storeSession()

      renderApp('/')

      expect(screen.getByRole('status')).toHaveTextContent('Carregando')
      expect(
        screen.queryByRole('heading', { name: 'Entrar' }),
      ).not.toBeInTheDocument()
    })

    it('shows the dashboard once the stored session is confirmed', async () => {
      storeSession()
      fetchMock.mockResolvedValueOnce(jsonResponse(alice))
      const { store } = renderApp('/')

      await restore(store)

      expect(
        await screen.findByRole('heading', { name: 'Painel' }),
      ).toBeInTheDocument()
    })

    it('sends the visitor to the login page when the stored session is refused', async () => {
      storeSession()
      fetchMock.mockImplementation(() =>
        Promise.resolve(jsonResponse({ detail: 'Token expired' }, 401)),
      )
      const { store } = renderApp('/')

      await restore(store)

      expect(
        await screen.findByRole('heading', { name: 'Entrar' }),
      ).toBeInTheDocument()
    })

    it('sends a signed-in visitor from the login page to the dashboard', async () => {
      storeSession()
      fetchMock.mockResolvedValueOnce(jsonResponse(alice))
      const { store } = renderApp('/login')

      await restore(store)

      expect(
        await screen.findByRole('heading', { name: 'Painel' }),
      ).toBeInTheDocument()
    })
  })
})
