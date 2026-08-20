import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'

import {
  getTopics,
  startDailyPractice,
  startQuickReview,
  startRandomTest,
  startTopicPractice,
} from '../api/practice'
import { ErrorNotice } from '../components/ErrorNotice'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { PageHeader } from '../components/PageHeader'
import { useAuth } from '../features/auth/useAuth'

export function PracticeStartPage() {
  const { session } = useAuth()
  const accessToken = session?.access_token
  const navigate = useNavigate()
  const [randomQuestionCount, setRandomQuestionCount] = useState(10)
  const topics = useQuery({
    queryKey: ['topics'],
    queryFn: ({ signal }) => getTopics(accessToken!, signal),
    enabled: Boolean(accessToken),
  })
  const daily = useMutation({
    mutationFn: () => startDailyPractice(accessToken!),
    onSuccess: (practiceSession) => navigate(practiceSession.status === 'completed' ? `/practice/${practiceSession.id}/complete` : `/practice/${practiceSession.id}`),
  })
  const topicPractice = useMutation({
    mutationFn: (topicId: string) => startTopicPractice(accessToken!, topicId),
    onSuccess: (practiceSession) => navigate(`/practice/${practiceSession.id}`),
  })
  const quickReview = useMutation({
    mutationFn: () => startQuickReview(accessToken!),
    onSuccess: (practiceSession) => navigate(`/practice/${practiceSession.id}`),
  })
  const randomTest = useMutation({
    mutationFn: () => startRandomTest(accessToken!, randomQuestionCount),
    onSuccess: (practiceSession) => navigate(`/practice/${practiceSession.id}`),
  })

  if (topics.isPending) {
    return <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8 lg:py-10"><LoadingSkeleton rows={4} /></div>
  }
  if (topics.isError) {
    return <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8 lg:py-10"><ErrorNotice message={topics.error.message} /></div>
  }

  return (
    <div className="mx-auto max-w-6xl px-5 py-8 sm:px-8 lg:py-10">
      <PageHeader
        description="Choose the adaptive daily session or spend ten questions strengthening one category."
        eyebrow="Practice"
        title="What would you like to work on?"
      />
      <section className="mt-8 rounded-[2rem] bg-ink p-6 text-white sm:p-8">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-100">Recommended</p>
        <h2 className="mt-3 text-3xl font-extrabold">Today’s adaptive practice</h2>
        <p className="mt-3 max-w-2xl leading-7 text-slate-300">A balanced ten-question session that prioritizes weak, missed, and unseen material.</p>
        <button className="mt-6 min-h-12 w-full rounded-2xl bg-teal-500 px-6 font-extrabold hover:bg-teal-400 disabled:opacity-60 sm:w-auto" disabled={daily.isPending} onClick={() => daily.mutate()} type="button">
          {daily.isPending ? 'PREPARING…' : 'START DAILY PRACTICE'}
        </button>
      </section>
      <section className="mt-5 grid gap-4 md:grid-cols-2">
        <article className="rounded-3xl border border-teal-200 bg-teal-50 p-6">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">Keep going</p>
          <h2 className="mt-2 text-2xl font-extrabold text-ink">Quick Review</h2>
          <p className="mt-2 leading-7 text-slate-600">
            Another adaptive set of 10 questions. Start it as often as you like, even after today’s daily goal.
          </p>
          <button
            className="mt-5 min-h-12 w-full rounded-2xl bg-teal-600 px-6 font-extrabold text-white hover:bg-teal-700 disabled:opacity-60 sm:w-auto"
            disabled={quickReview.isPending}
            onClick={() => quickReview.mutate()}
            type="button"
          >
            {quickReview.isPending ? 'PREPARING…' : 'START QUICK REVIEW'}
          </button>
        </article>

        <article className="rounded-3xl border border-slate-200 bg-white p-6 shadow-card">
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-sky-700">Mixed practice</p>
          <h2 className="mt-2 text-2xl font-extrabold text-ink">Random Test</h2>
          <p className="mt-2 leading-7 text-slate-600">
            Build a fresh test from random questions across the full question bank.
          </p>
          <div className="mt-5 grid gap-3 sm:grid-cols-[auto_1fr] sm:items-end">
            <label className="block">
              <span className="block text-sm font-bold text-ink">Questions</span>
              <select
                className="mt-2 min-h-12 w-full rounded-xl border border-slate-300 bg-white px-4 font-bold text-ink sm:w-auto"
                onChange={(event) => setRandomQuestionCount(Number(event.target.value))}
                value={randomQuestionCount}
              >
                {[10, 20, 30, 50].map((count) => (
                  <option key={count} value={count}>{count}</option>
                ))}
              </select>
            </label>
            <button
              className="min-h-12 w-full rounded-2xl bg-ink px-6 font-extrabold text-white hover:bg-slate-800 disabled:opacity-60 sm:w-auto"
              disabled={randomTest.isPending}
              onClick={() => randomTest.mutate()}
              type="button"
            >
              {randomTest.isPending ? 'PREPARING…' : 'START RANDOM TEST'}
            </button>
          </div>
        </article>
      </section>
      {(daily.error ?? topicPractice.error ?? quickReview.error ?? randomTest.error) ? (
        <div className="mt-5">
          <ErrorNotice message={(daily.error ?? topicPractice.error ?? quickReview.error ?? randomTest.error)!.message} />
        </div>
      ) : null}
      <section className="mt-10">
        <h2 className="text-2xl font-extrabold text-ink">Practice by category</h2>
        <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {topics.data.map((topic) => (
            <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-card" key={topic.id}>
              <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal-700">{topic.question_count} questions</p>
              <h3 className="mt-2 text-lg font-extrabold text-ink">{topic.name}</h3>
              <p className="mt-2 text-sm text-slate-500">{topic.children.length} focused subtopics</p>
              <button className="mt-5 min-h-11 w-full rounded-xl border border-teal-200 px-4 font-bold text-teal-700 hover:bg-teal-50 disabled:opacity-60 sm:w-auto" disabled={topicPractice.isPending} onClick={() => topicPractice.mutate(topic.id)} type="button">Practice category</button>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
