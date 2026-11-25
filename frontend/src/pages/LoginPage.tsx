import { useState } from 'react'
import { useNavigate } from 'react-router'
import { login } from '../auth/authSlice'
import { useAppDispatch } from '../hooks'
import styles from './LoginPage.module.css'

function LoginPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  async function submit() {
    const result = await dispatch(login({ username, password }))
    if (login.fulfilled.match(result)) {
      navigate('/')
    }
  }

  return (
    <section className={`glass ${styles.card}`}>
      <h2>Entrar</h2>
      <form
        className={styles.form}
        onSubmit={(event) => {
          event.preventDefault()
          void submit()
        }}
      >
        <div className="field">
          <label htmlFor="username">Usuário</label>
          <input
            id="username"
            name="username"
            type="text"
            className="input"
            autoComplete="username"
            value={username}
            onChange={(event) => setUsername(event.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="password">Senha</label>
          <input
            id="password"
            name="password"
            type="password"
            className="input"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </div>
        <button type="submit" className="btn btn-primary">
          Entrar
        </button>
      </form>
    </section>
  )
}

export default LoginPage
