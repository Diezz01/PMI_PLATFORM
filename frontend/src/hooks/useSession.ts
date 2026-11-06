import type { AuthSession } from '../services/auth'
import { useEffect, useRef, useState } from 'react'
import { getSession, logout as logoutRequest } from '../services/auth'

export function useSession() {
  const [session, setSession] = useState<AuthSession | null>(null)
  const [checkingSession, setCheckingSession] = useState(true)
  const [sessionError, setSessionError] = useState('')
  const [isSigningOut, setIsSigningOut] = useState(false)
  const [signOutError, setSignOutError] = useState('')
  const signingOutRef = useRef(false)

  useEffect(() => {
    let active = true

    async function restoreSession() {
      try {
        const restoredSession = await getSession()

        if (active) {
          setSession(restoredSession)
          setSessionError('')
        }
      } catch (error) {
        if (active) {
          setSessionError(
            error instanceof Error
              ? error.message
              : 'Unable to check your session.',
          )
        }
      } finally {
        if (active) {
          setCheckingSession(false)
        }
      }
    }

    void restoreSession()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!session) return

    const expiresAt = session.expires_at * 1000
    let timer: number | undefined

    function checkExpiration() {
      const remaining = expiresAt - Date.now()

      if (timer !== undefined) {
        window.clearTimeout(timer)
      }

      if (remaining <= 0) {
        setSession(null)
        return
      }

      timer = window.setTimeout(
        checkExpiration,
        Math.min(remaining, 2_147_483_647),
      )
    }

    timer = window.setTimeout(checkExpiration, 0)

    window.addEventListener('focus', checkExpiration)
    document.addEventListener('visibilitychange', checkExpiration)

    return () => {
      if (timer !== undefined) {
        window.clearTimeout(timer)
      }

      window.removeEventListener('focus', checkExpiration)
      document.removeEventListener('visibilitychange', checkExpiration)
    }
  }, [session])

  function completeLogin(nextSession: AuthSession) {
    setSession(nextSession)
    setSessionError('')
    setSignOutError('')
  }

  async function signOut(): Promise<boolean> {
    if (signingOutRef.current) return false

    signingOutRef.current = true
    setIsSigningOut(true)
    setSignOutError('')

    try {
      await logoutRequest()

      setSession(null)
      setSessionError('')

      return true
    } catch (error) {
      setSignOutError(
        error instanceof Error
          ? error.message
          : 'Unable to sign out. Please try again.',
      )

      return false
    } finally {
      signingOutRef.current = false
      setIsSigningOut(false)
    }
  }


  return {
  session,
  completeLogin,
  checkingSession,
  sessionError,
  signOut,
  isSigningOut,
  signOutError,
}
}

