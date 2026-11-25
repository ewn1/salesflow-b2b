export type Theme = 'dark' | 'light'

const STORAGE_KEY = 'salesflow.theme'
const DEFAULT_THEME: Theme = 'dark'

// localStorage is outside our control, so a stored value is only trusted
// after it is checked against the themes we actually support.
function isTheme(value: unknown): value is Theme {
  return value === 'dark' || value === 'light'
}

export function getTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY)
  return isTheme(stored) ? stored : DEFAULT_THEME
}

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute('data-theme', theme)
}

export function setTheme(theme: Theme) {
  localStorage.setItem(STORAGE_KEY, theme)
  applyTheme(theme)
}

// Runs once at startup: shows the remembered theme without saving anything.
export function initTheme() {
  applyTheme(getTheme())
}
