import { useEffect, useMemo, useState, type ReactNode } from 'react'
import type { AuthError, Session } from '@supabase/supabase-js'

import { supabase } from '../../api/supabase'
import { AuthContext, type AuthContextValue } from './auth-context'

interface AuthProviderProps {
  children: ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!supabase) {
      setLoading(false)
      return undefined
    }

    let active = true
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      if (active) {
        setSession(nextSession)
      }
    })

    void supabase.auth
      .getSession()
      .then(({ data }) => {
        if (active) {
          setSession(data.session)
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false)
        }
      })

    return () => {
      active = false
      subscription.unsubscribe()
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user: session?.user ?? null,
      session,
      loading,
      isConfigured: supabase !== null,
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
      async signOut(): Promise<AuthError | null> {
        if (!supabase) {
          throw new Error('Supabase authentication is not configured.')
        }
        const { error } = await supabase.auth.signOut()
        return error
      },
    }),
    [loading, session],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
