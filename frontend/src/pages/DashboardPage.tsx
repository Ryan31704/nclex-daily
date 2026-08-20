import { useMemo } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router-dom'

import {
  getDashboard,
  getProgress,
  getTopics,
  startDailyPractice,
  startQuickReview,
} from '../api/practice'
import { EmptyState } from '../components/EmptyState'
import { ErrorNotice } from '../components/ErrorNotice'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { PageHeader } from '../components/PageHeader'
import { ProgressBar } from '../components/ProgressBar'
import { StatCard } from '../components/StatCard'
import { StreakBadge } from '../components/StreakBadge'
import { TopicProgressCard } from '../components/TopicProgressCard'
import { XpBadge } from '../components/XpBadge'
import { useAuth } from '../features/auth/useAuth'
import { buildCategoryProgress } from '../utils/progress'

function greetingForCurrentTime(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

export function DashboardPage() {
  const { session, user } = useAuth()
  const accessToken = session?.access_token
  const navigate = useNavigate()

  const dashboard = useQuery({
    queryKey: ['dashboard', user?.id],
    queryFn: ({ signal }) => getDashboard(accessToken!, signal),
    enabled: Boolean(accessToken),
  })
  const topics = useQuery({
    queryKey: ['topics'],
    queryFn: ({ signal }) => getTopics(accessToken!, signal),
    enabled: Boolean(accessToken),
  })
  const progress = useQuery({
    queryKey: ['progress', user?.id],
    queryFn: ({ signal }) => getProgress(accessToken!, signal),
    enabled: Boolean(accessToken),
  })
  const openPracticeSession = (practiceSession: {
    id: string
    status: string
  }) => {
    navigate(
      practiceSession.status === 'completed'
        ? `/practice/${practiceSession.id}/complete`
        : `/practice/${practiceSession.id}`,
    )
  }
  const startSession = useMutation({
    mutationFn: () => startDailyPractice(accessToken!),
    onSuccess: openPracticeSession,
  })
  const quickReview = useMutation({
    mutationFn: () => startQuickReview(accessToken!),
    onSuccess: openPracticeSession,
  })

  const categoryProgress = useMemo(
    () => buildCategoryProgress(topics.data ?? [], progress.data?.topics ?? []),
    [progress.data?.topics, topics.data],
  )
  const dailySession = dashboard.data?.daily_session
  const ctaLabel =
    dailySession?.status === 'completed'
      ? 'START A QUICK REVIEW'
      : dailySession?.questions_completed
        ? 'CONTINUE TODAY’S PRACTICE'
        : 'START TODAY’S PRACTICE'

  if (dashboard.isPending || topics.isPending || progress.isPending) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:py-10">
        <LoadingSkeleton rows={4} />
      </div>
    )
  }

  const firstError = dashboard.error ?? topics.error ?? progress.error
  if (firstError) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:py-10">
        <ErrorNotice
          message={firstError.message}
          onRetry={() => {
            void Promise.all([dashboard.refetch(), topics.refetch(), progress.refetch()])
          }}
        />
      </div>
    )
  }

  const data = dashboard.data!
  const progressData = progress.data!
  const accuracy = progressData.questions_answered
    ? Math.round((progressData.correct_questions / progressData.questions_answered) * 100)
    : 0

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:py-10">
      <PageHeader
        action={
          <div className="flex flex-wrap gap-2">
            <StreakBadge days={data.current_streak} />
            <XpBadge xp={data.total_xp} />
          </div>
        }
        eyebrow="Your study home"
        title={`${greetingForCurrentTime()}, ${data.display_name}`}
      />

      <section className="mt-8 grid gap-4 sm:grid-cols-2 xl:grid-cols-4" aria-label="Study statistics">
        <StatCard detail={`Best: ${data.longest_streak} days`} icon="🔥" label="Current streak" tone="coral" value={`${data.current_streak} days`} />
        <StatCard icon="★" label="Total XP" tone="gold" value={data.total_xp.toLocaleString()} />
        <StatCard icon="✓" label="Questions answered" tone="blue" value={data.questions_answered.toLocaleString()} />
        <StatCard detail={`${accuracy}% accuracy`} icon="↗" label="Overall mastery" value={`${Math.round(data.overall_mastery)}%`} />
      </section>

      <section className="relative mt-6 overflow-hidden rounded-[2rem] bg-ink p-6 text-white shadow-xl shadow-slate-900/10 sm:p-8">
        <div aria-hidden="true" className="absolute -right-12 -top-16 h-52 w-52 rounded-full bg-teal-500/20 blur-2xl" />
        <div className="relative max-w-2xl">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-100">
            {dailySession?.status === 'completed' ? 'Daily goal complete' : 'Today’s practice'}
          </p>
          <h2 className="mt-3 text-3xl font-extrabold tracking-tight">
            {dailySession?.status === 'completed'
              ? 'You showed up today. Nice work.'
              : 'Ten focused questions. One stronger nurse.'}
          </h2>
          <p className="mt-3 max-w-xl leading-7 text-slate-300">
            {dailySession
              ? `${dailySession.questions_completed} of ${dailySession.target_question_count} questions completed.`
              : 'Your session adapts toward weaker topics while keeping the whole exam in view.'}
          </p>
          {dailySession && dailySession.status !== 'completed' ? (
            <div className="mt-5 max-w-md">
              <ProgressBar
                label="Daily practice completion"
                value={(dailySession.questions_completed / dailySession.target_question_count) * 100}
              />
            </div>
          ) : null}
          <div className="mt-7 flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-center">
            <button
              className="min-h-12 w-full rounded-2xl bg-teal-500 px-6 py-3 font-extrabold text-white shadow-lg shadow-teal-950/30 transition hover:bg-teal-400 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
              disabled={startSession.isPending || quickReview.isPending}
              onClick={() =>
                dailySession?.status === 'completed'
                  ? quickReview.mutate()
                  : startSession.mutate()
              }
              type="button"
            >
              {startSession.isPending || quickReview.isPending ? 'PREPARING…' : ctaLabel}
            </button>
            {dailySession?.status === 'completed' ? (
              <Link
                className="inline-flex min-h-12 w-full items-center justify-center rounded-2xl px-4 font-bold text-teal-100 hover:bg-white/10 sm:w-auto"
                to={`/practice/${dailySession.id}/complete`}
              >
                View today’s results
              </Link>
            ) : null}
            <span className="text-center text-sm font-semibold text-slate-400 sm:text-left">About 10 minutes</span>
          </div>
          {startSession.isError || quickReview.isError ? (
            <p className="mt-4 text-sm font-semibold text-rose-200" role="alert">
              {(startSession.error ?? quickReview.error)?.message}
            </p>
          ) : null}
        </div>
      </section>

      <div className="mt-10 grid gap-8 xl:grid-cols-[0.8fr_1.2fr]">
        <section>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">Focus next</p>
              <h2 className="mt-2 text-2xl font-extrabold text-ink">Weakest topics</h2>
            </div>
            <Link className="text-sm font-bold text-teal-700" to="/progress">View all</Link>
          </div>
          <div className="mt-5 space-y-3">
            {data.weakest_topics.length ? (
              data.weakest_topics.map((item) => (
                <Link
                  key={item.topic.id}
                  className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 transition hover:border-teal-300"
                  to={`/topics/${item.topic.slug}`}
                >
                  <div>
                    <p className="font-extrabold text-ink">{item.topic.name}</p>
                    <p className="mt-1 text-sm text-slate-500">{item.attempted_questions} attempts · {item.classification}</p>
                  </div>
                  <span className="text-lg font-extrabold text-teal-700">{Math.round(item.mastery_score)}%</span>
                </Link>
              ))
            ) : (
              <EmptyState
                description="Finish your first session and we’ll highlight the topics that deserve extra attention."
                icon="◎"
                title="Your focus list is waiting"
              />
            )}
          </div>
        </section>

        <section>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">Roadmap</p>
              <h2 className="mt-2 text-2xl font-extrabold text-ink">NCLEX progress</h2>
            </div>
            <Link className="text-sm font-bold text-teal-700" to="/progress">Explore roadmap</Link>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
            {categoryProgress.slice(0, 3).map((category) => (
              <TopicProgressCard category={category} key={category.id} />
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
