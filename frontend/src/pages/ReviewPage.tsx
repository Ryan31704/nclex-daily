import { useMemo, useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import { getMissedQuestions, getTopics, startMissedQuestionReview } from '../api/practice'
import { EmptyState } from '../components/EmptyState'
import { ErrorNotice } from '../components/ErrorNotice'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { PageHeader } from '../components/PageHeader'
import { useAuth } from '../features/auth/useAuth'
import { formatRelativeDate } from '../utils/progress'

export function ReviewPage() {
  const { session, user } = useAuth()
  const accessToken = session?.access_token
  const navigate = useNavigate()
  const [topicId, setTopicId] = useState<string | null>(null)
  const topics = useQuery({
    queryKey: ['topics'],
    queryFn: ({ signal }) => getTopics(accessToken!, signal),
    enabled: Boolean(accessToken),
  })
  const missed = useQuery({
    queryKey: ['missed', user?.id, topicId],
    queryFn: ({ signal }) => getMissedQuestions(accessToken!, topicId, signal),
    enabled: Boolean(accessToken),
  })
  const retry = useMutation({
    mutationFn: (questionId: string) =>
      startMissedQuestionReview(accessToken!, questionId),
    onSuccess: (practiceSession) => navigate(`/practice/${practiceSession.id}`),
  })
  const filterOptions = useMemo(
    () => (topics.data ?? []).flatMap((group) => group.children),
    [topics.data],
  )

  if (topics.isPending || missed.isPending) {
    return <div className="mx-auto max-w-5xl px-5 py-8 sm:px-8 lg:py-10"><LoadingSkeleton rows={4} /></div>
  }
  const error = topics.error ?? missed.error
  if (error) {
    return <div className="mx-auto max-w-5xl px-5 py-8 sm:px-8 lg:py-10"><ErrorNotice message={error.message} /></div>
  }
  const missedItems = missed.data ?? []

  return (
    <div className="mx-auto max-w-5xl px-5 py-8 sm:px-8 lg:py-10">
      <PageHeader
        action={
          <label className="block min-w-56">
            <span className="sr-only">Filter missed questions by topic</span>
            <select
              className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 font-semibold text-ink"
              onChange={(event) => setTopicId(event.target.value || null)}
              value={topicId ?? ''}
            >
              <option value="">All topics</option>
              {filterOptions.map((topic) => (
                <option key={topic.id} value={topic.id}>{topic.name}</option>
              ))}
            </select>
          </label>
        }
        description="Retry recent misses as fresh attempts. Correcting one later never overwrites the original record."
        eyebrow="Review"
        title="Learn from missed questions"
      />
      {retry.isError ? <div className="mt-5"><ErrorNotice message={retry.error.message} /></div> : null}
      <section className="mt-8 space-y-4">
        {missedItems.length ? (
          missedItems.map((item, index) => (
            <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-card sm:p-6" key={item.attempt_id}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <p className="text-xs font-bold uppercase tracking-[0.15em] text-rose-700">Missed question {index + 1}</p>
                <p className="text-sm font-semibold text-slate-400">{formatRelativeDate(item.attempted_at)}</p>
              </div>
              <h2 className="mt-4 text-xl font-extrabold leading-8 text-ink">{item.question.question_text}</h2>
              <p className="mt-3 text-sm font-semibold text-teal-700">{item.question.topic.name}</p>
              <div className="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-slate-100 pt-5">
                <p className="text-sm text-slate-500">Your previous response is preserved in your attempt history.</p>
                <button
                  className="min-h-11 rounded-xl bg-ink px-5 font-bold text-white hover:bg-slate-800 disabled:opacity-60"
                  disabled={retry.isPending}
                  onClick={() => retry.mutate(item.question.id)}
                  type="button"
                >
                  Retry question
                </button>
              </div>
            </article>
          ))
        ) : (
          <EmptyState
            action={<button className="rounded-xl bg-teal-600 px-5 py-3 font-bold text-white" onClick={() => navigate('/practice')} type="button">Start practice</button>}
            description="Questions leave this list after your most recent attempt is correct."
            icon="✓"
            title="No missed questions to review"
          />
        )}
      </section>
    </div>
  )
}
