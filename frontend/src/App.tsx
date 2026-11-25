import { Outlet } from 'react-router'
import styles from './App.module.css'
import { logout } from './auth/authSlice'
import { useAppDispatch, useAppSelector } from './hooks'

function App() {
  const dispatch = useAppDispatch()
  const status = useAppSelector((state) => state.auth.status)

  return (
    <div className={styles.shell}>
      <header className={`glass ${styles.header}`}>
        <h1>Sales Flow B2B</h1>
        {status === 'authenticated' && (
          <button
            type="button"
            className="btn"
            onClick={() => dispatch(logout())}
          >
            Sair
          </button>
        )}
      </header>
      <main className={styles.main}>
        <Outlet />
      </main>
    </div>
  )
}

export default App
