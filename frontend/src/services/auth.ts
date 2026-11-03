export async function login(email: string,password: string,): Promise<string> {
  const body = new URLSearchParams({
    //Need to use username field even if the login is made with email 
    //because in the backend OAuth2PasswordRequestForm is used
    username: email,
    password,
  })

  let response: Response

  try {
    response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body,
      signal: AbortSignal.timeout(15000),
    })
  } catch {
    throw new Error(
      'Unable to reach the server. Please check your connection and try again.',
    )
  }

  if (response.status === 401) {
    throw new Error('Incorrect email or password.')
  }

  if (response.status === 422) {
    throw new Error('Please check your email and password.')
  }

  if (response.status >= 500) {
    throw new Error(
      'The service is temporarily unavailable. Please try again later.',
    )
  }

  if (!response.ok) {
    throw new Error('Unable to sign in. Please try again.')
  }

  const data: unknown = await response.json().catch(() => null)

  if (
    typeof data !== 'object' ||
    data === null ||
    !('access_token' in data) ||
    typeof data.access_token !== 'string' ||
    !data.access_token.trim() ||
    !('token_type' in data) ||
    data.token_type !== 'bearer'
  ) {
    throw new Error(
      'The server returned an unexpected response. Please try again.',
    )
  }

  return data.access_token
}

export async function register(email: string,password: string): Promise<void> {
  let response: Response
  try {
    response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
      signal: AbortSignal.timeout(15000),
    })
  } catch {
    throw new Error(
      'Unable to confirm registration. Please check your connection.',
    )
  }

  if (response.status === 400 || response.status === 409) {
    throw new Error(
      'This email address is already registered. Please sign in.',
    )
  }

  if (response.status === 422) {
    throw new Error(
      'Please check your email address and password requirements.',
    )
  }

  if (response.status >= 500) {
    throw new Error(
      'The service is temporarily unavailable. Please try again later.',
    )
  }

  if (!response.ok) {
    throw new Error('Unable to create your account. Please try again.')
  }
}