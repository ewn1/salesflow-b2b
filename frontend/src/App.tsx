import styles from './App.module.css'
import { Outlet } from 'react-router'

function App() {
  return (
    <>
      <div className={styles.shell}>
        <header className={`glass ${styles.header}`}>
          <h1>Sales Flow B2B</h1>
        </header>
        <main className={styles.main}>
          <Outlet />
        </main>
      </div>
    </>
  )
}

export default App
