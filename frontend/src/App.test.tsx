import { act, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { getAccessToken, saveTokens } from './auth/tokenStorage'
import { restoreSession } from './store'
import { jsonResponse, setupFetchMock } from './test/http'
import { renderApp } from './test/renderApp'

const alice = { id: 1, username: 'alice', email: 'alice@example.com' }

describe('header', () => {
  const fetchMock = setupFetchMock()

  it('offers no logout button to an anonymous visitor', () => {
    renderApp('/login')

    expect(
      screen.queryByRole('button', { name: 'Sair' }),
    ).not.toBeInTheDocument()
  })

  it('lets any visitor switch the theme', () => {
    renderApp('/login')

    expect(
      screen.getByRole('button', { name: 'Usar tema claro' }),
    ).toBeInTheDocument()
  })

  it('lets a signed-in user log out', async () => {
    const user = userEvent.setup()
    saveTokens({ access: 'access-1', refresh: 'refresh-1' })
    fetchMock.mockResolvedValueOnce(jsonResponse(alice))
    const { store } = renderApp('/')
    await act(() => restoreSession(store))

    await user.click(await screen.findByRole('button', { name: 'Sair' }))

    expect(
      await screen.findByRole('heading', { name: 'Entrar' }),
    ).toBeInTheDocument()
    expect(getAccessToken()).toBeNull()
  })
})
