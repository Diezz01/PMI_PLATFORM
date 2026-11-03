import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { register } from '../services/auth'
import {
  validateEmail,
  validateRegistrationPassword,
} from '../utils/authValidation'
import styles from '../css/loginForm.module.css'

type RegisterFormProps = {
  onRegistered: () => void
  onBackToLogin: () => void
}

const fields = [
  {
    name: 'email',
    label: 'Email',
    type: 'email',
    autoComplete: 'username',
  },
  {
    name: 'password',
    label: 'Password',
    type: 'password',
    autoComplete: 'new-password',
  },
  {
    name: 'confirmPassword',
    label: 'Confirm password',
    type: 'password',
    autoComplete: 'new-password',
  },
] as const

type FieldName = (typeof fields)[number]['name']
type Errors = Partial<Record<FieldName, string>>

function getInput(form: HTMLFormElement, name: FieldName) {
  return form.elements.namedItem(name) as HTMLInputElement
}

function validateForm(form: HTMLFormElement): Errors {
  const email = getInput(form, 'email')
  const password = getInput(form, 'password').value
  const confirmation = getInput(form, 'confirmPassword').value

  let confirmationError = ''

  if (!confirmation) {
    confirmationError = 'Repeat your password.'
  } else if (confirmation !== password) {
    confirmationError = 'Passwords do not match.'
  }

  return {
    email: validateEmail(email),
    password: validateRegistrationPassword(password),
    confirmPassword: confirmationError,
  }
}

function RegisterForm({
  onRegistered,
  onBackToLogin,
}: RegisterFormProps) {
  const [errors, setErrors] = useState<Errors>({})
  const [touched, setTouched] = useState<
    Partial<Record<FieldName, boolean>>
  >({})
  const [submitted, setSubmitted] = useState(false)
  const [serverError, setServerError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const submittingRef = useRef(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (submittingRef.current) return

    const form = event.currentTarget
    const nextErrors = validateForm(form)

    setSubmitted(true)
    setErrors(nextErrors)
    setServerError('')

    const firstInvalid = fields.find(
      (field) => Boolean(nextErrors[field.name]),
    )

    if (firstInvalid) {
      getInput(form, firstInvalid.name).focus()
      return
    }

    const email = getInput(form, 'email').value
    const password = getInput(form, 'password').value

    submittingRef.current = true
    setIsSubmitting(true)

    try {
      await register(email, password)
      onRegistered()
    } catch (error) {
      setServerError(
        error instanceof Error
          ? error.message
          : 'Unable to create your account. Please try again.',
      )
    } finally {
      submittingRef.current = false
      setIsSubmitting(false)
    }
  }

  return (
    <section className={styles.card} aria-labelledby="register-title">
      <h1 id="register-title" className={styles.title}>
        Create your account
      </h1>

      <form
        className={styles.form}
        noValidate
        onSubmit={handleSubmit}
        aria-busy={isSubmitting}
        onChange={(event) => {
          const input = event.target

          if (!(input instanceof HTMLInputElement)) return

          const name = input.name as FieldName

          setTouched((previous) => ({
            ...previous,
            [name]: true,
          }))
          setErrors(validateForm(event.currentTarget))
          setServerError('')
        }}
      >
        {fields.map((field) => {
          const checked = submitted || Boolean(touched[field.name])
          const error = checked ? errors[field.name] : ''
          const inputId = `register-${field.name}`
          const errorId = `${inputId}-error`

          const descriptionIds = [
            field.name === 'password' ? 'register-password-hint' : '',
            error ? errorId : '',
          ].filter(Boolean).join(' ')

          return (
            <div key={field.name} className={styles.field}>
              <label htmlFor={inputId} className={styles.label}>
                {field.label}
              </label>

              <input
                id={inputId}
                name={field.name}
                type={field.type}
                autoComplete={field.autoComplete}
                autoCapitalize="none"
                spellCheck={false}
                required
                readOnly={isSubmitting}
                className={styles.input}
                aria-invalid={Boolean(error)}
                data-valid={checked && !errors[field.name]}
                aria-describedby={descriptionIds || undefined}
              />


              <p
                id={errorId}
                className={styles.error}
                aria-live="polite"
              >
                {error}
              </p>
            </div>
          )
        })}

        <button type="submit" className={styles.submitButton}>
          {isSubmitting ? 'Creating account...' : 'Create account'}
        </button>

        <p className={styles.error} role="alert">
          {serverError}
        </p>

        <button
          type="button"
          className={styles.linkButton}
          onClick={onBackToLogin}
          disabled={isSubmitting}
        >
          Already have an account? Sign in
        </button>
      </form>
    </section>
  )
}

export default RegisterForm