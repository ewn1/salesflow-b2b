import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { renderApp } from './test/renderApp'

describe('routes', () => {
  it.each([
    ['/', 'Painel'],
    ['/login', 'Entrar'],
    ['/register', 'Criar conta'],
  ])('renders the page for %s', (path, title) => {
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
})
