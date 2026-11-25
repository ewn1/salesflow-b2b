import { useState } from 'react'
import { useNavigate } from 'react-router'
import { login, type AuthError } from '../auth/authSlice'
import { useAppDispatch } from '../hooks'
import styles from './LoginPage.module.css'

function loginErrorMessage(error: AuthError | undefined) {
  if (error?.status === 401) {
    return 'Usuário ou senha incorretos.'
  }
  if (error?.status === null) {
    return 'Não foi possível conectar ao servidor. Tente novamente.'
  }
  return 'Não foi possível entrar agora. Tente novamente em instantes.'
}

function LoginPage() {
  const dispatch = useAppDispatch()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  async function submit() {
    setErrorMessage(null)
    const result = await dispatch(login({ username, password }))
    if (login.fulfilled.match(result)) {
      navigate('/')
    } else {
      setErrorMessage(loginErrorMessage(result.payload))
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
        {errorMessage && (
          <p role="alert" className="field-error">
            {errorMessage}
          </p>
        )}
        <button type="submit" className="btn btn-primary">
          Entrar
        </button>
      </form>
    </section>
  )
}

export default LoginPage
