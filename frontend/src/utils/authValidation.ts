export function validateEmail(input: HTMLInputElement): string {
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

export function validateRegistrationPassword(value: string): string {
  const missing: string[] = []

  if (Array.from(value).length < 8) {
    missing.push('at least 8 characters')
  }

  if (!/[A-Z]/.test(value)) {
    missing.push('an uppercase letter')
  }

  if (!/[a-z]/.test(value)) {
    missing.push('a lowercase letter')
  }

  if (!/[0-9]/.test(value)) {
    missing.push('a number')
  }

  if (!/[\x21-\x2f\x3a-\x40\x5b-\x60\x7b-\x7e]/.test(value)) {
    missing.push('a special character')
  }

  return missing.length
    ? `Password must contain ${missing.join(', ')}.`
    : ''
}