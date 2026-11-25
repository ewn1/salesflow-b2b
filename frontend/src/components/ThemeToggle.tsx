import { useState } from 'react'
import { getTheme, setTheme, type Theme } from '../theme'

export default function ThemeToggle() {
  const [theme, setCurrentTheme] = useState<Theme>(getTheme)

  function toggle() {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    setTheme(next)
    setCurrentTheme(next)
  }

  return (
    <button type="button" className="btn" onClick={toggle}>
      {theme === 'dark' ? 'Usar tema claro' : 'Usar tema escuro'}
    </button>
  )
}
