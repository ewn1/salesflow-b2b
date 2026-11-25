import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { jsonResponse, setupFetchMock } from '../test/http'
import { renderApp } from '../test/renderApp'

const alice = { id: 1, username: 'alice', email: 'alice@example.com' }

async function signIn(username: string, password: string) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText('Usuário'), username)
  await user.type(screen.getByLabelText('Senha'), password)
  await user.click(screen.getByRole('button', { name: 'Entrar' }))
}

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

    await signIn('alice', 'secret-pass')

    expect(
      await screen.findByRole('heading', { name: 'Painel' }),
    ).toBeInTheDocument()
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      username: 'alice',
      password: 'secret-pass',
    })
  })

  it.each([
    [
      'the credentials are refused',
      () =>
        Promise.resolve(
          jsonResponse({ detail: 'No active account found' }, 401),
        ),
      'Usuário ou senha incorretos.',
    ],
    [
      'the network fails',
      () => Promise.reject(new TypeError('Failed to fetch')),
      'Não foi possível conectar ao servidor. Tente novamente.',
    ],
    [
      'the server fails',
      () => Promise.resolve(jsonResponse({ detail: 'Server error' }, 500)),
      'Não foi possível entrar agora. Tente novamente em instantes.',
    ],
  ])('shows an alert when %s', async (_reason, answer, message) => {
    fetchMock.mockImplementation(answer)
    renderApp('/login')

    await signIn('alice', 'wrong-pass')

    expect(await screen.findByRole('alert')).toHaveTextContent(message)
    expect(
      screen.queryByRole('heading', { name: 'Painel' }),
    ).not.toBeInTheDocument()
  })

  it('disables the button and shows progress while the login is in flight', async () => {
    let release: (response: Response) => void = () => {}
    fetchMock.mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          release = resolve
        }),
    )
    renderApp('/login')

    await signIn('alice', 'secret-pass')

    expect(screen.getByRole('button', { name: 'Entrando...' })).toBeDisabled()

    release(jsonResponse({ detail: 'No active account found' }, 401))
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Entrar' })).toBeEnabled()
  })
})
