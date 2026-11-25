import { beforeEach, describe, expect, it } from 'vitest'
import { getTheme, initTheme, setTheme } from './theme'

const KEY = 'salesflow.theme'

function appliedTheme() {
  return document.documentElement.getAttribute('data-theme')
}

describe('theme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('defaults to dark when nothing is stored', () => {
    expect(getTheme()).toBe('dark')
  })

  it('returns the stored theme', () => {
    localStorage.setItem(KEY, 'light')

    expect(getTheme()).toBe('light')
  })

  it('ignores an unknown stored value', () => {
    localStorage.setItem(KEY, 'purple')

    expect(getTheme()).toBe('dark')
  })

  it('stores the choice and applies it to the page', () => {
    setTheme('light')

    expect(localStorage.getItem(KEY)).toBe('light')
    expect(appliedTheme()).toBe('light')
  })

  it('applies the stored theme on startup without writing anything', () => {
    localStorage.setItem(KEY, 'light')

    initTheme()

    expect(appliedTheme()).toBe('light')
  })

  it('applies the default theme on startup when nothing is stored', () => {
    initTheme()

    expect(appliedTheme()).toBe('dark')
    expect(localStorage.getItem(KEY)).toBeNull()
  })
})
