import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { jsonResponse, setupFetchMock } from '../test/http'
import { renderApp } from '../test/renderApp'

const alice = { id: 1, username: 'alice', email: 'alice@example.com' }

describe('LoginPage', () => {
  const fetchMock = setupFetchMock()

  it('renders the username and password fields and the submit button', () => {
    renderApp('/login')

    expect(screen.getByLabelText('Usuário')).toBeInTheDocument()
    expect(screen.getByLabelText('Senha')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeInTheDocument()
  })

  it('logs in with the typed credentials and goes to the dashboard', async () => {
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse({ access: 'access-1', refresh: 'refresh-1' }),
      )
      .mockResolvedValueOnce(jsonResponse(alice))
    renderApp('/login')
    const user = userEvent.setup()

    await user.type(screen.getByLabelText('Usuário'), 'alice')
    await user.type(screen.getByLabelText('Senha'), 'secret-pass')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(
      await screen.findByRole('heading', { name: 'Painel' }),
    ).toBeInTheDocument()
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      username: 'alice',
      password: 'secret-pass',
    })
  })
})
