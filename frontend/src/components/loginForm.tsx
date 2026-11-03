import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import styles from './../css/loginForm.module.css'
import { login } from './../services/auth'
import { validateEmail } from '../utils/authValidation'
import type { AuthSession } from '../services/auth'

function validatePassword(value: string): string {
  if (!value) {
    return 'Enter your password.'
  }

  if (value.length < 8) {
    return 'Your password must contain at least 8 characters.'
  }

  return ''
}

type LoginFormProps = {
  onLoginSuccess: (session: AuthSession) => void
}

function LoginForm({ onLoginSuccess }: LoginFormProps) {
  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)

  const [emailError, setEmailError] = useState('Enter your email address.')
  const [passwordError, setPasswordError] = useState('Enter your password.')

  const [emailTouched, setEmailTouched] = useState(false)
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [status, setStatus] = useState('')

  const submittingRef = useRef(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (submittingRef.current) return

    const emailInput = emailRef.current
    const passwordInput = passwordRef.current

    if (!emailInput || !passwordInput) return

    const nextEmailError = validateEmail(emailInput)
    const nextPasswordError = validatePassword(passwordInput.value)

    setEmailError(nextEmailError)
    setPasswordError(nextPasswordError)
    setEmailTouched(true)
    setPasswordTouched(true)
    setStatus('')

    if (nextEmailError) {
      emailInput.focus()
      return
    }

    if (nextPasswordError) {
      passwordInput.focus()
      return
    }

    submittingRef.current = true

    try {
      const session = await login(
      emailInput.value,
      passwordInput.value)

    onLoginSuccess(session)
    } catch (error) {
      setStatus(
        error instanceof Error
          ? error.message
          : 'Unable to sign in. Please try again.',
      )
    } finally {
      submittingRef.current = false
    }
  }

  return (
    <section className={styles.card} aria-labelledby="login-title">
      <h1 id="login-title" className={styles.title}>
        Sign in to the platform
      </h1>

      <form className={styles.form} noValidate onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label htmlFor="login-email" className={styles.label}>
            Email
          </label>

          <input
            ref={emailRef}
            id="login-email"
            name="email"
            type="email"
            autoComplete="username"
            autoCapitalize="none"
            spellCheck={false}
            required
            className={styles.input}
            aria-invalid={emailTouched && Boolean(emailError)}
            data-valid={emailTouched && !emailError}
            aria-describedby={
              emailTouched && emailError ? 'email-error' : undefined
            }
            onChange={(event) => {
              setEmailTouched(true)
              setEmailError(validateEmail(event.currentTarget))
              setStatus('')
            }}
            onBlur={(event) => {
              setEmailTouched(true)
              setEmailError(validateEmail(event.currentTarget))
            }}
          />

          <p id="email-error" className={styles.error} aria-live="polite">
            {emailTouched ? emailError : ''}
          </p>
        </div>

        <div className={styles.field}>
          <label htmlFor="login-password" className={styles.label}>
            Password
          </label>

          <input
            ref={passwordRef}
            id="login-password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            minLength={8}
            className={styles.input}
            aria-invalid={passwordTouched && Boolean(passwordError)}
            data-valid={passwordTouched && !passwordError}
            aria-describedby={
              passwordTouched && passwordError
                ? 'password-hint password-error'
                : 'password-hint'
            }
            onChange={(event) => {
              setPasswordTouched(true)
              setPasswordError(validatePassword(event.currentTarget.value))
              setStatus('')
            }}
            onBlur={(event) => {
              setPasswordTouched(true)
              setPasswordError(validatePassword(event.currentTarget.value))
            }}
          />

          <p id="password-hint" className={styles.hint}>
            At least 8 characters.
          </p>

          <p id="password-error" className={styles.error} aria-live="polite">
            {passwordTouched ? passwordError : ''}
          </p>
        </div>

        <button type="submit" className={styles.submitButton}>
          Sign in
        </button>

        <p className={styles.error} role="alert">
          {status}
        </p>
      </form>
    </section>
  )
}

export default LoginForm