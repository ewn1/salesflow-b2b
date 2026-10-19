import { render, screen } from '@testing-library/react'
import { createMemoryRouter } from 'react-router'
import { RouterProvider } from 'react-router/dom'
import { describe, expect, it } from 'vitest'
import { routes } from './routes'

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] })
  render(<RouterProvider router={router} />)
}

describe('routes', () => {
  it.each([
    ['/', 'Painel'],
    ['/login', 'Entrar'],
    ['/register', 'Criar conta'],
  ])('renders the page for %s', (path, title) => {
    renderAt(path)

    expect(screen.getByRole('heading', { name: title })).toBeInTheDocument()
  })

  it('renders a not found page for unknown paths', () => {
    renderAt('/does-not-exist')

    expect(
      screen.getByRole('heading', { name: 'Página não encontrada' }),
    ).toBeInTheDocument()
  })

  it('keeps the product name visible on every page', () => {
    renderAt('/login')

    expect(
      screen.getByRole('heading', { level: 1, name: 'Sales Flow B2B' }),
    ).toBeInTheDocument()
  })
})
