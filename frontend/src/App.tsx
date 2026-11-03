//MODULES
import LoginForm from './components/loginForm'
import Dashboard from './components/Dashboard'
import RegisterForm from './components/RegistrationForm'
import { useSession } from './hooks/useSession'

//CSS
import styles from './css/App.module.css'
import authStyles from './css/loginForm.module.css'

//ASSETS
import logoUnicam from './assets/Logo_unicam-removebg-preview.png'

import { useState } from 'react'




function App() {
 const {session,setSession,checkingSession,sessionError} = useSession()
  const [authView, setAuthView] = useState<'login' | 'register'>('login')
  const [registrationMessage, setRegistrationMessage] = useState('')
  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.brand}>
            <img
                src={logoUnicam}
                alt="University of Camerino"
                className={styles.unicamLogo}
              />

            <div>
              <p className={styles.brandName}>UNICAM PMI Platform</p>
              <p className={styles.brandDescription}>
                Estimation of the post-mortem interval
              </p>
            </div>
          </div>

          <span className={styles.context}>Forensic Medicine</span>
        </div>
      </header>
      <main className={styles.main}>
        {checkingSession ? (
          <p role="status">Checking your session...</p>
        ) : sessionError ? (
          <section className={authStyles.card}>
            <p className={authStyles.error} role="alert">
              {sessionError}
            </p>

            <button
              type="button"
              className={authStyles.linkButton}
              onClick={() => window.location.reload()}
            >
              Try again
            </button>
          </section>
        ) : session ? (
          <Dashboard />
        ) : (
          <div className={styles.authPanel}>
            {authView === 'register' ? (
              <RegisterForm
                onRegistered={() => {
                  setRegistrationMessage(
                    'Registration completed successfully. You can now sign in.',
                  )
                  setAuthView('login')
                }}
                onBackToLogin={() => {
                  setRegistrationMessage('')
                  setAuthView('login')
                }}
              />
            ) : (
              <>
                {registrationMessage && (
                  <p className={authStyles.success} role="status">
                    {registrationMessage}
                  </p>
                )}

                <LoginForm onLoginSuccess={setSession} />

                <p className={authStyles.navigation}>
                  <button
                    type="button"
                    className={authStyles.linkButton}
                    onClick={() => {
                      setRegistrationMessage('')
                      setAuthView('register')
                    }}
                  >
                    Don't have an account? Create one
                  </button>
                </p>
              </>
            )}
          </div>
        )}
      </main>
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <p className={styles.footerBrand}>UNICAM PMI Platform</p>
          <p className={styles.footerDescription}>
            Master Thesis Project · Computer Science Department
          </p>
        </div>
      </footer>
    </div>
  )
}

export default App