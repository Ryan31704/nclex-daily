import { createContext } from 'react'
import type { AuthError, Session, User } from '@supabase/supabase-js'

export interface SignUpResult {
  error: AuthError | null
  emailConfirmationRequired: boolean
}

export interface AuthContextValue {
  user: User | null
  session: Session | null
  loading: boolean
  isConfigured: boolean
  passwordSetupRequired: boolean
  signIn: (email: string, password: string) => Promise<AuthError | null>
  signUp: (
    email: string,
    password: string,
    displayName: string,
  ) => Promise<SignUpResult>
  verifyInvite: (tokenHash: string) => Promise<AuthError | null>
  setPassword: (password: string) => Promise<AuthError | null>
  signOut: () => Promise<AuthError | null>
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
