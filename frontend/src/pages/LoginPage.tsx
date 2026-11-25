import styles from './LoginPage.module.css'

function LoginPage() {
  return (
    <section className={`glass ${styles.card}`}>
      <h2>Entrar</h2>
      <form className={styles.form}>
        <div className="field">
          <label htmlFor="username">Usuário</label>
          <input
            id="username"
            name="username"
            type="text"
            className="input"
            autoComplete="username"
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
