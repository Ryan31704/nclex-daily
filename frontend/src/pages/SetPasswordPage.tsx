import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { authConfigError } from '../api/supabase'
import { LoadingScreen } from '../components/LoadingScreen'
import { useAuth } from '../features/auth/useAuth'

type InviteStatus = 'checking' | 'ready' | 'invalid'

export function SetPasswordPage() {
  const [searchParams] = useSearchParams()
  const tokenHash = searchParams.get('token_hash')
  const [status, setStatus] = useState<InviteStatus>('checking')
  const [password, setPasswordValue] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const {
    user,
    loading,
    isConfigured,
    passwordSetupRequired,
    verifyInvite,
    setPassword,
  } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (loading) {
      return
    }
    if (user && passwordSetupRequired) {
      setStatus('ready')
      return
    }
    if (!tokenHash || !isConfigured) {
      setStatus('invalid')
      return
    }

    let active = true
    void verifyInvite(tokenHash).then((inviteError) => {
      if (!active) {
        return
      }
      if (inviteError) {
        setError(
          'This invitation link is invalid or has expired. Ask the beta administrator to send a new invitation.',
        )
        setStatus('invalid')
      } else {
        setStatus('ready')
      }
    })

    return () => {
      active = false
    }
  }, [isConfigured, loading, passwordSetupRequired, tokenHash, user, verifyInvite])

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)

    if (password.length < 8) {
      setError('Use a password with at least 8 characters.')
      return
    }
    if (password !== confirmation) {
      setError('The passwords do not match.')
      return
    }

    setSubmitting(true)
    try {
      const passwordError = await setPassword(password)
      if (passwordError) {
        setError(passwordError.message)
        return
      }
      navigate('/dashboard', { replace: true })
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : 'Your password could not be saved.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (loading || status === 'checking') {
    return <LoadingScreen />
  }

  return (
    <main className="grid min-h-screen place-items-center bg-canvas px-5 py-12">
      <section className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-200/50 sm:p-9">
        <Link className="text-xl font-extrabold tracking-tight text-ink" to="/">
          NCLEX <span className="text-teal-600">Daily</span>
        </Link>

        <p className="mt-8 text-sm font-bold uppercase tracking-[0.18em] text-teal-700">
          Private beta invitation
        </p>
        <h1 className="mt-3 text-3xl font-bold tracking-tight text-ink">
          {status === 'ready' ? 'Create your password' : 'Invitation unavailable'}
        </h1>

        {status === 'invalid' ? (
          <div className="mt-5">
            <p className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm leading-6 text-red-800" role="alert">
              {error ?? authConfigError ?? 'Open the invitation link from your email to continue.'}
            </p>
            <Link
              className="mt-5 inline-flex min-h-12 w-full items-center justify-center rounded-xl border border-slate-300 px-5 py-3 font-bold text-ink transition hover:border-teal-500"
              to="/login"
            >
              Return to Log In
            </Link>
          </div>
        ) : (
          <>
            <p className="mt-3 leading-7 text-slate-600">
              Choose a password for {user?.email ?? 'your account'}. You will use it
              whenever you return to NCLEX Daily.
            </p>

            <form className="mt-7 space-y-5" onSubmit={handleSubmit}>
              <label className="block">
                <span className="text-sm font-semibold text-ink">Password</span>
                <input
                  autoComplete="new-password"
                  className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-ink outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
                  minLength={8}
                  onChange={(event) => setPasswordValue(event.target.value)}
                  placeholder="At least 8 characters"
                  required
                  type="password"
                  value={password}
                />
              </label>

              <label className="block">
                <span className="text-sm font-semibold text-ink">Confirm password</span>
                <input
                  autoComplete="new-password"
                  className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 text-ink outline-none transition focus:border-teal-600 focus:ring-4 focus:ring-teal-100"
                  minLength={8}
                  onChange={(event) => setConfirmation(event.target.value)}
                  placeholder="Enter it again"
                  required
                  type="password"
                  value={confirmation}
                />
              </label>

              {error ? (
                <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">
                  {error}
                </p>
              ) : null}

              <button
                className="min-h-12 w-full rounded-xl bg-teal-600 px-5 py-3 font-bold text-white shadow-lg shadow-teal-600/20 transition hover:bg-teal-700 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={submitting}
                type="submit"
              >
                {submitting ? 'Saving password…' : 'Create Password & Continue'}
              </button>
            </form>
          </>
        )}
      </section>
    </main>
  )
}
