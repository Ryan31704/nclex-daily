import { useEffect, useMemo, useState, type ReactNode } from 'react'
import type { AuthError, Session } from '@supabase/supabase-js'

import {
  clearInviteSetupPending,
  isInviteSetupPending,
  markInviteSetupPending,
  requestPersistentStorage,
  supabase,
} from '../../api/supabase'
import { AuthContext, type AuthContextValue } from './auth-context'

interface AuthProviderProps {
  children: ReactNode
}

let inviteVerificationPromise: Promise<AuthError | null> | null = null

export function AuthProvider({ children }: AuthProviderProps) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const [passwordSetupRequired, setPasswordSetupRequired] = useState(
    isInviteSetupPending,
  )

  useEffect(() => {
    if (!supabase) {
      setLoading(false)
      return undefined
    }

    const authClient = supabase
    let active = true
    let sessionSyncPromise: Promise<void> | null = null
    const syncStoredSession = () => {
      if (!sessionSyncPromise) {
        sessionSyncPromise = authClient.auth
          .getSession()
          .then(({ data }) => {
            if (active) {
              setSession(data.session)
              if (data.session) {
                void requestPersistentStorage()
              }
            }
          })
          .finally(() => {
            sessionSyncPromise = null
          })
        }
      return sessionSyncPromise
    }
    const handlePageShow = () => {
      void syncStoredSession()
    }
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        void syncStoredSession()
      }
    }
    const {
      data: { subscription },
    } = authClient.auth.onAuthStateChange((_event, nextSession) => {
      if (active) {
        setSession(nextSession)
        if (nextSession) {
          void requestPersistentStorage()
        }
      }
    })

    window.addEventListener('pageshow', handlePageShow)
    document.addEventListener('visibilitychange', handleVisibilityChange)

    void syncStoredSession()
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })

    return () => {
      active = false
      window.removeEventListener('pageshow', handlePageShow)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      subscription.unsubscribe()
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user: session?.user ?? null,
      session,
      loading,
      isConfigured: supabase !== null,
      passwordSetupRequired,
      async signIn(email: string, password: string): Promise<AuthError | null> {
        if (!supabase) {
          throw new Error('Supabase authentication is not configured.')
        }
        const { error } = await supabase.auth.signInWithPassword({ email, password })
        return error
      },
      async signUp(email: string, password: string, displayName: string) {
        if (!supabase) {
          throw new Error('Supabase authentication is not configured.')
        }
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: { display_name: displayName.trim() },
            emailRedirectTo: `${window.location.origin}/dashboard`,
          },
        })
        return {
          error,
          emailConfirmationRequired: !error && data.session === null,
        }
      },
      async verifyInvite(tokenHash: string): Promise<AuthError | null> {
        if (!supabase) {
          throw new Error('Supabase authentication is not configured.')
        }

        if (!inviteVerificationPromise) {
          inviteVerificationPromise = supabase.auth
            .verifyOtp({ token_hash: tokenHash, type: 'invite' })
            .then(({ error }) => {
              if (!error) {
                markInviteSetupPending()
                setPasswordSetupRequired(true)
              }
              return error
            })
        }

        return inviteVerificationPromise
      },
      async setPassword(password: string): Promise<AuthError | null> {
        if (!supabase) {
          throw new Error('Supabase authentication is not configured.')
        }

        const { error } = await supabase.auth.updateUser({ password })
        if (!error) {
          clearInviteSetupPending()
          setPasswordSetupRequired(false)
          inviteVerificationPromise = null
        }
        return error
      },
      async signOut(): Promise<AuthError | null> {
        if (!supabase) {
          throw new Error('Supabase authentication is not configured.')
        }
        const { error } = await supabase.auth.signOut()
        return error
      },
    }),
    [loading, passwordSetupRequired, session],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
