export type AuthSession = {
  user: {
    id: number
    email: string
  }
  expires_at: number
}

async function readSession(response: Response): Promise<AuthSession> {
  const data: unknown = await response.json().catch(() => null)

  if (
    typeof data !== 'object' ||
    data === null ||
    !('user' in data) ||
    typeof data.user !== 'object' ||
    data.user === null ||
    !('id' in data.user) ||
    typeof data.user.id !== 'number' ||
    !Number.isInteger(data.user.id) ||
    !('email' in data.user) ||
    typeof data.user.email !== 'string' ||
    !('expires_at' in data) ||
    typeof data.expires_at !== 'number' ||
    !Number.isSafeInteger(data.expires_at)
  ) {
    throw new Error('The server returned an unexpected response.')
  }

  return {
    user: {
      id: data.user.id,
      email: data.user.email,
    },
    expires_at: data.expires_at,
  }
}

export async function getSession(): Promise<AuthSession | null> {
  let response: Response

  try {
    response = await fetch('/api/auth/session', {
      credentials: 'same-origin',
      cache: 'no-store',
      signal: AbortSignal.timeout(15000),
    })
  } catch {
    throw new Error(
      'Unable to check your session. Please check your connection.',
    )
  }

  if (response.status === 401) {
    return null
  }

  if (!response.ok) {
    throw new Error(
      'Unable to check your session. Please try again later.',
    )
  }

  return readSession(response)
}

export async function login(
  email: string,
  password: string,
): Promise<AuthSession> {
  let response: Response

  try {
    response = await fetch('/api/auth/session', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-PMI-Request': '1',
      },
      body: new URLSearchParams({
        username: email,
        password,
      }),
      signal: AbortSignal.timeout(15000),
    })
  } catch {
    throw new Error(
      'Unable to reach the server. Please check your connection.',
    )
  }

  if (response.status === 401) {
    throw new Error('Incorrect email or password.')
  }

  if (response.status === 403) {
    throw new Error('Sign-in is not allowed from this application address.')
  }

  if (response.status === 422) {
    throw new Error('Please check your email and password.')
  }

  if (!response.ok) {
    throw new Error('Unable to sign in. Please try again later.')
  }

  return readSession(response)
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

export async function logout(): Promise<void> {
  let response: Response

  try {
    response = await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'X-PMI-Request': '1',
      },
      signal: AbortSignal.timeout(15000),
    })
  } catch {
    throw new Error(
      'Unable to confirm sign-out. Please check your connection and try again.',
    )
  }

  if (!response.ok) {
    throw new Error('Unable to sign out. Please try again.')
  }
}