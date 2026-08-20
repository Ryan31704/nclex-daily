import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'

import { getDashboard, getPracticeSession, startQuickReview } from '../api/practice'
import { BrandLogo } from '../components/BrandLogo'
import { ErrorNotice } from '../components/ErrorNotice'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { ProgressBar } from '../components/ProgressBar'
import { StreakBadge } from '../components/StreakBadge'
import { XpBadge } from '../components/XpBadge'
import { useAuth } from '../features/auth/useAuth'
import type { CompleteSessionResponse } from '../types/practice'

export function SessionCompletePage() {
  const { session: authSession, user } = useAuth()
  const accessToken = authSession?.access_token
  const { sessionId = '' } = useParams<{ sessionId: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const completion = location.state as CompleteSessionResponse | null
  const practiceSession = useQuery({
    queryKey: ['practice-session', sessionId],
    queryFn: ({ signal }) => getPracticeSession(accessToken!, sessionId, signal),
    enabled: Boolean(accessToken && sessionId),
  })
  const dashboard = useQuery({
    queryKey: ['dashboard', user?.id],
    queryFn: ({ signal }) => getDashboard(accessToken!, signal),
    enabled: Boolean(accessToken),
  })
  const quickReview = useMutation({
    mutationFn: () => startQuickReview(accessToken!),
    onSuccess: (practiceSession) => navigate(`/practice/${practiceSession.id}`),
  })

  if (practiceSession.isPending || dashboard.isPending) {
    return <main className="min-h-screen bg-canvas px-5 py-8"><div className="mx-auto max-w-2xl"><LoadingSkeleton rows={4} /></div></main>
  }
  const error = practiceSession.error ?? dashboard.error
  if (error) {
    return <main className="min-h-screen bg-canvas px-5 py-8"><div className="mx-auto max-w-2xl"><ErrorNotice message={error.message} /></div></main>
  }

  const result = practiceSession.data!
  const dashboardData = dashboard.data!
  const scorePercent = result.target_question_count
    ? (result.correct_count / result.target_question_count) * 100
    : 0
  const completionTitle = {
    daily: 'Daily goal complete',
    topic: 'Topic practice complete',
    quick_review: 'Quick Review complete',
    random: 'Random test complete',
  }[result.practice_type]

  return (
    <main className="min-h-screen bg-canvas px-5 py-6 sm:px-8">
      <div className="mx-auto max-w-3xl">
        <BrandLogo />
        <section className="mt-8 overflow-hidden rounded-[2rem] border border-slate-200 bg-white shadow-card">
          <div className="bg-ink px-6 py-10 text-center text-white sm:px-10">
            <span aria-hidden="true" className="text-6xl">🎉</span>
            <p className="mt-5 text-xs font-bold uppercase tracking-[0.2em] text-teal-100">Session complete</p>
            <h1 className="mt-3 text-4xl font-extrabold tracking-tight">
              {completionTitle}
            </h1>
            <p className="mt-3 text-slate-300">You made meaningful progress today.</p>
          </div>
          <div className="p-6 sm:p-10">
            <div className="grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-slate-50 p-5 text-center">
                <p className="text-sm font-semibold text-slate-500">Correct</p>
                <p className="mt-2 text-3xl font-extrabold text-ink">{result.correct_count} / {result.target_question_count}</p>
              </div>
              <div className="rounded-2xl bg-amber-50 p-5 text-center">
                <p className="text-sm font-semibold text-amber-700">XP earned</p>
                <p className="mt-2 text-3xl font-extrabold text-amber-800">{result.xp_earned}</p>
              </div>
              <div className="rounded-2xl bg-orange-50 p-5 text-center">
                <p className="text-sm font-semibold text-orange-700">Current streak</p>
                <p className="mt-2 text-3xl font-extrabold text-orange-800">{dashboardData.current_streak} days</p>
              </div>
            </div>
            <div className="mt-7">
              <ProgressBar label="Session accuracy" showValue value={scorePercent} />
            </div>
            <div className="mt-6 flex flex-wrap justify-center gap-2">
              <XpBadge xp={completion?.total_xp ?? dashboardData.total_xp} />
              <StreakBadge days={completion?.current_streak ?? dashboardData.current_streak} />
            </div>
            {quickReview.isError ? <div className="mt-6"><ErrorNotice message={quickReview.error.message} /></div> : null}
            <div className="mt-8 grid gap-3 sm:grid-cols-3">
              <Link className="inline-flex min-h-12 items-center justify-center rounded-2xl bg-teal-600 px-6 font-extrabold text-white hover:bg-teal-700" to="/dashboard">Back to Dashboard</Link>
              <button
                className="min-h-12 rounded-2xl bg-ink px-6 font-extrabold text-white hover:bg-slate-800 disabled:opacity-60"
                disabled={quickReview.isPending}
                onClick={() => quickReview.mutate()}
                type="button"
              >
                {quickReview.isPending ? 'PREPARING…' : 'Quick Review'}
              </button>
              <Link className="inline-flex min-h-12 items-center justify-center rounded-2xl border border-slate-200 px-6 font-extrabold text-ink hover:border-teal-300" to="/practice">More options</Link>
            </div>
          </div>
        </section>
      </div>
    </main>
  )
}
