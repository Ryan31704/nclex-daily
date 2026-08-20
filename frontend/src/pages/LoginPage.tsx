import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'

import { authConfigError } from '../api/supabase'
import { useAuth } from '../features/auth/useAuth'

type AuthMode = 'login' | 'signup'

function readableAuthError(message: string): string {
  const normalized = message.toLowerCase()
  if (normalized.includes('invalid login credentials')) {
    return 'That email and password combination was not recognized.'
  }
  if (normalized.includes('email not confirmed')) {
    return 'Confirm your email address before logging in.'
  }
  if (normalized.includes('user already registered')) {
    return 'An account already exists for that email. Try logging in instead.'
  }
  if (normalized.includes('password')) {
    return 'Use a password with at least 8 characters.'
  }
  return message
}

export function LoginPage() {
  const [searchParams] = useSearchParams()
  const initialMode: AuthMode = searchParams.get('mode') === 'signup' ? 'signup' : 'login'
  const [mode, setMode] = useState<AuthMode>(initialMode)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { signIn, signUp, isConfigured } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const switchMode = (nextMode: AuthMode) => {
    setMode(nextMode)
    setError(null)
    setNotice(null)
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setNotice(null)

    if (password.length < 8) {
      setError('Use a password with at least 8 characters.')
      return
    }
    if (mode === 'signup' && !displayName.trim()) {
      setError('Enter the name you would like to see on your dashboard.')
      return
    }

    setSubmitting(true)
    try {
      if (mode === 'login') {
        const authError = await signIn(email.trim(), password)
        if (authError) {
          setError(readableAuthError(authError.message))
          return
        }
        const redirectPath =
          (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ??
          '/dashboard'
        navigate(redirectPath, { replace: true })
      } else {
        const result = await signUp(email.trim(), password, displayName)
        if (result.error) {
          setError(readableAuthError(result.error.message))
          return
        }
        if (result.emailConfirmationRequired) {
          setNotice(
            'Account created. Check your email and follow the confirmation link, then log in.',
          )
        } else {
          navigate('/dashboard', { replace: true })
        }
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : 'Authentication failed.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <main className="grid min-h-screen bg-canvas lg:grid-cols-[1fr_1.05fr]">
      <section className="hidden bg-ink p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <Link className="text-xl font-extrabold tracking-tight" to="/">
          NCLEX <span className="text-teal-100">Daily</span>
        </Link>
        <div className="max-w-lg">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-teal-100">
            A calmer way to prepare
          </p>
          <h1 className="mt-5 text-5xl font-bold leading-tight">
            Small daily wins become exam-day confidence.
          </h1>
          <p className="mt-5 text-lg leading-8 text-slate-300">
            Practice consistently, learn from every rationale, and keep your weak
            topics in view.
          </p>
        </div>
        <p className="text-sm text-slate-400">Built for focused nursing students.</p>
      </section>

      <section className="flex items-center justify-center px-5 pb-[max(3rem,env(safe-area-inset-bottom))] pt-[max(2rem,env(safe-area-inset-top))] sm:px-10 sm:py-12">
        <div className="w-full max-w-md">
          <Link className="text-xl font-extrabold tracking-tight text-ink lg:hidden" to="/">
            NCLEX <span className="text-teal-600">Daily</span>
          </Link>

          <div
            className="mt-9 flex rounded-2xl bg-slate-100 p-1"
            aria-label="Authentication mode"
            role="group"
          >
            {(['login', 'signup'] as const).map((item) => (
              <button
                key={item}
                className={`min-h-11 flex-1 rounded-xl px-4 font-semibold transition ${
                  mode === item
                    ? 'bg-white text-ink shadow-sm'
                    : 'text-slate-500 hover:text-ink'
                }`}
                onClick={() => switchMode(item)}
                type="button"
              >
                {item === 'login' ? 'Log In' : 'Create Account'}
              </button>
            ))}
          </div>

          <h1 className="mt-8 text-3xl font-bold tracking-tight text-ink sm:mt-9 sm:text-4xl">
            {mode === 'login' ? 'Welcome back' : 'Start your study streak'}
          </h1>
          <p className="mt-2 text-slate-600">
            {mode === 'login'
              ? 'Continue building your NCLEX confidence.'
              : 'Create an account for personalized daily practice.'}
          </p>

          <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
            {mode === 'signup' ? (
              <label className="block">
                <span className="text-sm font-semibold text-ink">Display name</span>
                <input
                  autoComplete="name"
                  className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-ink outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
                  maxLength={100}
                  onChange={(event) => setDisplayName(event.target.value)}
                  placeholder="Alex"
                  required
                  type="text"
                  value={displayName}
                />
              </label>
            ) : null}

            <label className="block">
              <span className="text-sm font-semibold text-ink">Email</span>
              <input
                autoComplete="email"
                className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-ink outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                required
                type="email"
                value={email}
              />
            </label>

            <label className="block">
              <span className="text-sm font-semibold text-ink">Password</span>
              <input
                autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-ink outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
                minLength={8}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="At least 8 characters"
                required
                type="password"
                value={password}
              />
            </label>

            {authConfigError ? (
              <p className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900" role="alert">
                {authConfigError}
              </p>
            ) : null}
            {error ? (
              <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">
                {error}
              </p>
            ) : null}
            {notice ? (
              <p className="rounded-xl border border-teal-200 bg-teal-50 p-3 text-sm text-teal-800" role="status">
                {notice}
              </p>
            ) : null}

            <button
              className="min-h-12 w-full rounded-xl bg-teal-600 px-5 py-3 font-bold text-white shadow-lg shadow-teal-600/20 transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={submitting || !isConfigured}
              type="submit"
            >
              {submitting
                ? 'Please wait…'
                : mode === 'login'
                  ? 'Log In'
                  : 'Create Account'}
            </button>
          </form>
        </div>
      </section>
    </main>
  )
}
