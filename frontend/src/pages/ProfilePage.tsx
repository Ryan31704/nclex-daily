import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { getMyProfile } from '../api/profile'
import { ErrorNotice } from '../components/ErrorNotice'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { PageHeader } from '../components/PageHeader'
import { StatCard } from '../components/StatCard'
import { useAuth } from '../features/auth/useAuth'

export function ProfilePage() {
  const { session, user, signOut } = useAuth()
  const accessToken = session?.access_token
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const [loggingOut, setLoggingOut] = useState(false)
  const [logoutError, setLogoutError] = useState<string | null>(null)
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

  if (profile.isPending) {
    return <div className="mx-auto max-w-4xl px-5 py-8 sm:px-8 lg:py-10"><LoadingSkeleton rows={3} /></div>
  }
  if (profile.isError) {
    return <div className="mx-auto max-w-4xl px-5 py-8 sm:px-8 lg:py-10"><ErrorNotice message={profile.error.message} /></div>
  }

  const data = profile.data
  return (
    <div className="mx-auto max-w-4xl px-5 py-8 sm:px-8 lg:py-10">
      <PageHeader description="Your account and study totals." eyebrow="Profile" title={data.display_name} />
      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        <StatCard icon="🔥" label="Current streak" tone="coral" value={`${data.current_streak} days`} />
        <StatCard icon="★" label="Total XP" tone="gold" value={data.total_xp.toLocaleString()} />
        <StatCard icon="↗" label="Longest streak" tone="blue" value={`${data.longest_streak} days`} />
      </section>
      <section className="mt-6 rounded-3xl border border-slate-200 bg-white p-6 shadow-card">
        <h2 className="text-lg font-extrabold text-ink">Account</h2>
        <dl className="mt-5 grid gap-5 sm:grid-cols-2">
          <div><dt className="text-sm font-semibold text-slate-500">Email</dt><dd className="mt-1 break-all font-bold text-ink">{data.email}</dd></div>
          <div><dt className="text-sm font-semibold text-slate-500">Member since</dt><dd className="mt-1 font-bold text-ink">{new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(data.created_at))}</dd></div>
        </dl>
        {logoutError ? <div className="mt-5"><ErrorNotice message={logoutError} /></div> : null}
        <button className="mt-7 min-h-11 rounded-xl border border-rose-200 px-5 font-bold text-rose-700 hover:bg-rose-50 disabled:opacity-60" disabled={loggingOut} onClick={handleLogOut} type="button">
          {loggingOut ? 'Logging out…' : 'Log Out'}
        </button>
      </section>
    </div>
  )
}
