import { useMemo } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { getProgress, getTopics, startTopicPractice } from '../api/practice'
import { EmptyState } from '../components/EmptyState'
import { ErrorNotice } from '../components/ErrorNotice'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { PageHeader } from '../components/PageHeader'
import { ProgressBar } from '../components/ProgressBar'
import { useAuth } from '../features/auth/useAuth'
import { buildCategoryProgress, classificationFor, formatRelativeDate } from '../utils/progress'

export function TopicPage() {
  const { slug } = useParams<{ slug: string }>()
  const { session, user } = useAuth()
  const accessToken = session?.access_token
  const navigate = useNavigate()
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
  const startPractice = useMutation({
    mutationFn: (topicId: string) => startTopicPractice(accessToken!, topicId),
    onSuccess: (practiceSession) => navigate(`/practice/${practiceSession.id}`),
  })

  const resolved = useMemo(() => {
    const groups = topics.data ?? []
    const parent = groups.find((group) => group.slug === slug)
    if (parent) return { group: parent, selectedChildId: null }
    for (const group of groups) {
      const child = group.children.find((item) => item.slug === slug)
      if (child) return { group, selectedChildId: child.id }
    }
    return null
  }, [slug, topics.data])

  if (topics.isPending || progress.isPending) {
    return <div className="mx-auto max-w-5xl px-5 py-8 sm:px-8 lg:py-10"><LoadingSkeleton rows={4} /></div>
  }
  const error = topics.error ?? progress.error
  if (error) {
    return <div className="mx-auto max-w-5xl px-5 py-8 sm:px-8 lg:py-10"><ErrorNotice message={error.message} /></div>
  }
  if (!resolved) {
    return (
      <div className="mx-auto max-w-5xl px-5 py-8 sm:px-8 lg:py-10">
        <EmptyState
          action={<Link className="font-bold text-teal-700" to="/progress">Back to progress</Link>}
          description="This topic may have been renamed or disabled."
          title="Topic not found"
        />
      </div>
    )
  }

  const progressByTopic = new Map(progress.data!.topics.map((item) => [item.topic.id, item]))
  const visibleChildren = resolved.selectedChildId
    ? resolved.group.children.filter((child) => child.id === resolved.selectedChildId)
    : resolved.group.children
  const category = buildCategoryProgress([resolved.group], progress.data!.topics)[0]
  const selectedChild = resolved.selectedChildId
    ? resolved.group.children.find((child) => child.id === resolved.selectedChildId)
    : null
  const pageTitle = selectedChild?.name ?? resolved.group.name
  const practiceTopicId = selectedChild?.id ?? resolved.group.id

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 sm:px-8 lg:py-10">
      <Link className="text-sm font-bold text-teal-700" to="/progress">← Back to progress</Link>
      <div className="mt-6 rounded-[2rem] bg-ink p-6 text-white sm:p-8">
        <PageHeader
          action={
            <button
              className="min-h-12 rounded-2xl bg-teal-500 px-6 py-3 font-extrabold text-white hover:bg-teal-400 disabled:opacity-60"
              disabled={startPractice.isPending}
              onClick={() => startPractice.mutate(practiceTopicId)}
              type="button"
            >
              {startPractice.isPending ? 'PREPARING…' : 'PRACTICE THIS TOPIC'}
            </button>
          }
          description={`${selectedChild?.question_count ?? resolved.group.question_count} questions available`}
          eyebrow={selectedChild ? resolved.group.name : 'Category mastery'}
          inverted
          title={pageTitle}
        />
        <div className="mt-7 max-w-xl">
          <ProgressBar
            label={`${pageTitle} mastery`}
            showValue
            value={selectedChild ? progressByTopic.get(selectedChild.id)?.mastery_score ?? 0 : category.masteryScore}
          />
        </div>
      </div>
      {startPractice.isError ? <div className="mt-5"><ErrorNotice message={startPractice.error.message} /></div> : null}

      <section className="mt-10">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">Subtopics</p>
        <h2 className="mt-2 text-2xl font-extrabold text-ink">Choose your next focus</h2>
        <div className="mt-5 space-y-4">
          {visibleChildren.map((child) => {
            const item = progressByTopic.get(child.id)
            const mastery = item?.mastery_score ?? 0
            return (
              <article key={child.id} className="rounded-3xl border border-slate-200 bg-white p-5 shadow-card sm:p-6">
                <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <h3 className="text-lg font-extrabold text-ink">{child.name}</h3>
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold capitalize text-slate-600">
                        {item?.classification ?? classificationFor(0)}
                      </span>
                    </div>
                    <div className="mt-4 max-w-xl">
                      <ProgressBar label={`${child.name} mastery`} showValue size="sm" value={mastery} />
                    </div>
                    <p className="mt-3 text-sm text-slate-500">
                      {item?.attempted_questions ?? 0} attempts · {item?.correct_percentage ?? 0}% correct · {formatRelativeDate(item?.last_practiced_at ?? null)}
                    </p>
                  </div>
                  <button
                    className="min-h-11 shrink-0 rounded-xl border border-teal-200 px-5 py-2.5 font-bold text-teal-700 transition hover:bg-teal-50 disabled:opacity-60"
                    disabled={startPractice.isPending}
                    onClick={() => startPractice.mutate(child.id)}
                    type="button"
                  >
                    Practice
                  </button>
                </div>
              </article>
            )
          })}
        </div>
      </section>
    </div>
  )
}
