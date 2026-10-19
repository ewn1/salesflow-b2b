import { Outlet } from 'react-router'

function App() {
  return (
    <>
      <header>
        <h1>Sales Flow B2B</h1>
      </header>
      <main>
        <Outlet />
      </main>
    </>
  )
}

export default App
