import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it } from 'vitest'
import ThemeToggle from './ThemeToggle'

describe('ThemeToggle', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('offers the light theme when the page is dark', () => {
    render(<ThemeToggle />)

    expect(
      screen.getByRole('button', { name: 'Usar tema claro' }),
    ).toBeInTheDocument()
  })

  it('offers the dark theme when the stored theme is light', () => {
    localStorage.setItem('salesflow.theme', 'light')

    render(<ThemeToggle />)

    expect(
      screen.getByRole('button', { name: 'Usar tema escuro' }),
    ).toBeInTheDocument()
  })

  it('switches the theme, remembers it and offers the way back', async () => {
    const user = userEvent.setup()
    render(<ThemeToggle />)

    await user.click(screen.getByRole('button', { name: 'Usar tema claro' }))

    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
    expect(localStorage.getItem('salesflow.theme')).toBe('light')
    expect(
      screen.getByRole('button', { name: 'Usar tema escuro' }),
    ).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Usar tema escuro' }))

    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    expect(localStorage.getItem('salesflow.theme')).toBe('dark')
  })
})
