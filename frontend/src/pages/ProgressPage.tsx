import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getProgress, getTopics } from '../api/practice'
import { ErrorNotice } from '../components/ErrorNotice'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { PageHeader } from '../components/PageHeader'
import { StatCard } from '../components/StatCard'
import { TopicProgressCard } from '../components/TopicProgressCard'
import { useAuth } from '../features/auth/useAuth'
import { buildCategoryProgress } from '../utils/progress'

export function ProgressPage() {
  const { session, user } = useAuth()
  const accessToken = session?.access_token
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
  const categories = useMemo(
    () => buildCategoryProgress(topics.data ?? [], progress.data?.topics ?? []),
    [progress.data?.topics, topics.data],
  )

  if (topics.isPending || progress.isPending) {
    return <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:py-10"><LoadingSkeleton rows={5} /></div>
  }
  const error = topics.error ?? progress.error
  if (error) {
    return (
      <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:py-10">
        <ErrorNotice message={error.message} onRetry={() => void Promise.all([topics.refetch(), progress.refetch()])} />
      </div>
    )
  }

  const data = progress.data!
  const accuracy = data.questions_answered
    ? Math.round((data.correct_questions / data.questions_answered) * 100)
    : 0

  return (
    <div className="mx-auto max-w-7xl px-5 py-8 sm:px-8 lg:py-10">
      <PageHeader
        description="See where your recent practice is paying off and which categories deserve another focused session."
        eyebrow="Your roadmap"
        title="NCLEX progress"
      />
      <section className="mt-8 grid gap-4 sm:grid-cols-3" aria-label="Progress summary">
        <StatCard icon="◎" label="Overall mastery" value={`${Math.round(data.overall_mastery)}%`} />
        <StatCard icon="✓" label="Questions answered" tone="blue" value={data.questions_answered.toLocaleString()} />
        <StatCard icon="↗" label="Correct answers" tone="gold" value={`${accuracy}%`} />
      </section>
      <section className="mt-10">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">All categories</p>
            <h2 className="mt-2 text-2xl font-extrabold text-ink">Build every system</h2>
          </div>
          <p className="text-sm font-semibold text-slate-500">Recent attempts count more toward mastery</p>
        </div>
        <div className="mt-5 grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
          {categories.map((category) => (
            <TopicProgressCard category={category} key={category.id} />
          ))}
        </div>
      </section>
    </div>
  )
}
