import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import styles from './../css/loginForm.module.css'

function validateEmail(input: HTMLInputElement): string {
  const value = input.value

  if (!value.trim()) {
    return 'Enter your email address.'
  }

  if (/\s/.test(value)) {
    return 'Email addresses cannot contain spaces.'
  }

  const parts = value.split('@')

  if (parts.length !== 2) {
    return 'Enter an email address with one @ symbol.'
  }

  if (!parts[0]) {
    return 'Enter the part before the @ symbol.'
  }

  if (!parts[1]) {
    return 'Enter the domain after the @ symbol.'
  }

  const domain = parts[1]

  if (domain.endsWith('.')) {
    return 'The email domain cannot end with a dot.'
  }

  if (!domain.includes('.')) {
    return 'Enter a domain with a dot, such as example.com.'
  }

  if (domain.split('.').some((part) => !part)) {
    return 'Enter text between each dot in the email domain.'
  }

  if (input.validity.typeMismatch) {
    return 'Enter a valid email address, such as name@example.com.'
  }

  return ''
}

function validatePassword(value: string): string {
  if (!value) {
    return 'Enter your password.'
  }

  if (value.length < 8) {
    return 'Your password must contain at least 8 characters.'
  }

  return ''
}

function LoginForm() {
  const emailRef = useRef<HTMLInputElement>(null)
  const passwordRef = useRef<HTMLInputElement>(null)

  const [emailError, setEmailError] = useState('Enter your email address.')
  const [passwordError, setPasswordError] = useState('Enter your password.')

  const [emailTouched, setEmailTouched] = useState(false)
  const [passwordTouched, setPasswordTouched] = useState(false)
  const [status, setStatus] = useState('')

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

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

    setStatus('The fields are valid. Sign-in is not connected yet.')
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

        <p className={styles.status} role="status">
          {status}
        </p>
      </form>
    </section>
  )
}

export default LoginForm