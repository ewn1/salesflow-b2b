import { Outlet } from 'react-router'
import styles from './App.module.css'
import { logout } from './auth/authSlice'
import ThemeToggle from './components/ThemeToggle'
import { useAppDispatch, useAppSelector } from './hooks'

function App() {
  const dispatch = useAppDispatch()
  const status = useAppSelector((state) => state.auth.status)

  return (
    <div className={styles.shell}>
      <header className={`glass ${styles.header}`}>
        <h1>Sales Flow B2B</h1>
        <div className={styles.actions}>
          <ThemeToggle />
          {status === 'authenticated' && (
            <button
              type="button"
              className="btn"
              onClick={() => dispatch(logout())}
            >
              Sair
            </button>
          )}
        </div>
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}

export default App
