import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { getMyProfile } from '../api/profile'
import { useAuth } from '../features/auth/useAuth'

export function DashboardPage() {
  const { session, user, signOut } = useAuth()
  const [logoutError, setLogoutError] = useState<string | null>(null)
  const [loggingOut, setLoggingOut] = useState(false)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const accessToken = session?.access_token

  const profile = useQuery({
    queryKey: ['me', user?.id],
    queryFn: ({ signal }) => getMyProfile(accessToken!, signal),
    enabled: Boolean(accessToken),
  })

  const handleLogOut = async () => {
    setLoggingOut(true)
    setLogoutError(null)
    try {
      const error = await signOut()
      if (error) {
        setLogoutError(error.message)
        return
      }
      queryClient.clear()
      navigate('/login', { replace: true })
    } catch (error) {
      setLogoutError(error instanceof Error ? error.message : 'Unable to log out.')
    } finally {
      setLoggingOut(false)
    }
  }

  const displayName = profile.data?.display_name ?? user?.email?.split('@')[0] ?? 'Student'

  return (
    <main className="min-h-screen bg-canvas">
      <header className="border-b border-slate-200 bg-white px-5 py-4 sm:px-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
          <span className="text-xl font-extrabold tracking-tight text-ink">
            NCLEX <span className="text-teal-600">Daily</span>
          </span>
          <button
            className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-bold text-ink transition hover:border-teal-500 disabled:opacity-60"
            disabled={loggingOut}
            onClick={handleLogOut}
            type="button"
          >
            {loggingOut ? 'Logging out…' : 'Log Out'}
          </button>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14">
        <p className="font-semibold text-teal-700">Authentication connected</p>
        <h1 className="mt-2 text-4xl font-bold tracking-tight text-ink sm:text-5xl">
          Welcome, {displayName}
        </h1>
        <p className="mt-3 text-lg text-slate-600">
          Your secure study dashboard is ready for the quiz engine in the next phases.
        </p>

        {profile.isPending ? (
          <div className="mt-10 h-56 animate-pulse rounded-3xl bg-slate-200" aria-label="Loading profile" />
        ) : null}
        {profile.isError ? (
          <div className="mt-10 rounded-2xl border border-red-200 bg-red-50 p-5 text-red-800" role="alert">
            <p className="font-bold">We could not load your backend profile.</p>
            <p className="mt-1 text-sm">{profile.error.message}</p>
          </div>
        ) : null}
        {profile.data ? (
          <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card sm:col-span-2">
              <p className="text-sm font-semibold uppercase tracking-wider text-slate-500">Signed in as</p>
              <p className="mt-3 break-all text-xl font-bold text-ink">{profile.data.email}</p>
              <p className="mt-2 text-sm text-slate-500">Profile ID: {profile.data.id}</p>
            </article>
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card">
              <p className="text-sm font-semibold text-slate-500">Current streak</p>
              <p className="mt-3 text-3xl font-bold text-ink">{profile.data.current_streak} days</p>
            </article>
            <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card">
              <p className="text-sm font-semibold text-slate-500">Total XP</p>
              <p className="mt-3 text-3xl font-bold text-ink">{profile.data.total_xp}</p>
            </article>
          </div>
        ) : null}

        {logoutError ? (
          <p className="mt-6 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-800" role="alert">
            {logoutError}
          </p>
        ) : null}
      </section>
    </main>
  )
}
