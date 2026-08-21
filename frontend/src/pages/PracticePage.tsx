import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'

import {
  completePracticeSession,
  getPracticeSession,
  submitPracticeAnswer,
} from '../api/practice'
import { BrandLogo } from '../components/BrandLogo'
import { ErrorNotice } from '../components/ErrorNotice'
import { LoadingSkeleton } from '../components/LoadingSkeleton'
import { ProgressBar } from '../components/ProgressBar'
import { QuestionCard } from '../components/QuestionCard'
import { QuestionInteraction } from '../components/QuestionInteraction'
import { XpBadge } from '../components/XpBadge'
import { useAuth } from '../features/auth/useAuth'
import type { SubmitAnswerResponse } from '../types/practice'

export function PracticePage() {
  const { session: authSession, user } = useAuth()
  const accessToken = authSession?.access_token
  const { sessionId = '' } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)
  const [feedback, setFeedback] = useState<SubmitAnswerResponse | null>(null)
  const questionStartedAt = useRef(Date.now())
  const feedbackPanel = useRef<HTMLElement | null>(null)

  const practiceSession = useQuery({
    queryKey: ['practice-session', sessionId],
    queryFn: ({ signal }) => getPracticeSession(accessToken!, sessionId, signal),
    enabled: Boolean(accessToken && sessionId),
  })
  const firstUnansweredIndex = practiceSession.data?.questions.findIndex(
    (item) => !item.answered,
  ) ?? -1
  const currentIndex = selectedIndex ?? Math.max(firstUnansweredIndex, 0)
  const currentItem = practiceSession.data?.questions[currentIndex]

  useEffect(() => {
    questionStartedAt.current = Date.now()
  }, [currentItem?.question.id])

  useEffect(() => {
    if (feedback) {
      feedbackPanel.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
    }
  }, [feedback])

  useEffect(() => {
    if (practiceSession.data?.status === 'completed') {
      navigate(`/practice/${sessionId}/complete`, { replace: true })
    }
  }, [navigate, practiceSession.data?.status, sessionId])

  const submitAnswer = useMutation({
    mutationFn: (answer: unknown) =>
      submitPracticeAnswer(
        accessToken!,
        sessionId,
        currentItem!.question.id,
        answer,
        Date.now() - questionStartedAt.current,
      ),
    onSuccess: (result) => {
      setFeedback(result)
    },
  })
  const completeSession = useMutation({
    mutationFn: () => completePracticeSession(accessToken!, sessionId),
    onSuccess: (result) => {
      void Promise.all([
        queryClient.invalidateQueries({ queryKey: ['dashboard', user?.id] }),
        queryClient.invalidateQueries({ queryKey: ['progress', user?.id] }),
        queryClient.invalidateQueries({ queryKey: ['missed', user?.id] }),
      ])
      navigate(`/practice/${sessionId}/complete`, { replace: true, state: result })
    },
  })

  const chooseAnswer = (answer: unknown) => {
    if (submitAnswer.isPending || feedback) return
    setSelectedIndex(currentIndex)
    submitAnswer.mutate(answer)
  }

  const continuePractice = () => {
    if (!practiceSession.data) return
    const isFinalQuestion = currentIndex >= practiceSession.data.questions.length - 1
    if (isFinalQuestion) {
      completeSession.mutate()
      return
    }
    setSelectedIndex(currentIndex + 1)
    setFeedback(null)
  }

  if (practiceSession.isPending) {
    return <main className="min-h-screen bg-canvas px-5 py-8"><div className="mx-auto max-w-3xl"><LoadingSkeleton rows={4} /></div></main>
  }
  if (practiceSession.isError) {
    return <main className="min-h-screen bg-canvas px-5 py-8"><div className="mx-auto max-w-3xl"><ErrorNotice message={practiceSession.error.message} /></div></main>
  }

  const data = practiceSession.data
  if (!data) return null
  const allAnswered = firstUnansweredIndex === -1 && !feedback

  if (allAnswered) {
    return (
      <main className="grid min-h-screen place-items-center bg-canvas px-5 py-10">
        <div className="w-full max-w-xl rounded-[2rem] border border-slate-200 bg-white p-8 text-center shadow-card">
          <span aria-hidden="true" className="text-5xl">✓</span>
          <h1 className="mt-5 text-3xl font-extrabold text-ink">All answers are in</h1>
          <p className="mt-3 text-slate-500">Finish the session to save your daily bonus and streak.</p>
          {completeSession.isError ? <div className="mt-5"><ErrorNotice message={completeSession.error.message} /></div> : null}
          <button className="mt-7 min-h-12 rounded-2xl bg-teal-600 px-7 font-extrabold text-white disabled:opacity-60" disabled={completeSession.isPending} onClick={() => completeSession.mutate()} type="button">
            {completeSession.isPending ? 'FINISHING…' : 'FINISH SESSION'}
          </button>
        </div>
      </main>
    )
  }

  if (!currentItem) return null
  const completionPercent = ((currentIndex + (feedback ? 1 : 0)) / data.target_question_count) * 100

  return (
    <main className={`min-h-screen bg-canvas ${feedback ? 'pb-32' : ''}`}>
      <header className="border-b border-slate-200 bg-white px-4 pb-4 pt-[max(1rem,env(safe-area-inset-top))] sm:px-5">
        <div className="mx-auto flex max-w-5xl items-center justify-between gap-3">
          <BrandLogo compact />
          <Link className="rounded-xl px-4 py-2 text-sm font-bold text-slate-500 hover:bg-slate-50" to="/dashboard">
            Save & exit
          </Link>
        </div>
      </header>
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-5 sm:py-10">
        <div className="flex items-center justify-between gap-4">
          <p className="text-sm font-extrabold text-ink">Question {currentIndex + 1} of {data.target_question_count}</p>
          <XpBadge xp={data.xp_earned + (feedback?.xp_earned ?? 0)} />
        </div>
        <div className="mt-4">
          <ProgressBar label="Session progress" value={completionPercent} />
        </div>

        <div className="mt-7">
          <QuestionCard context={currentItem.question.case_study_markdown} question={currentItem.question.question_text} topic={currentItem.question.topic.name}>
            <QuestionInteraction disabled={submitAnswer.isPending || Boolean(feedback)} feedback={feedback} key={currentItem.question.id} onSubmit={chooseAnswer} question={currentItem.question} />
          </QuestionCard>
        </div>

        {submitAnswer.isError ? <div className="mt-5"><ErrorNotice message={submitAnswer.error.message} /></div> : null}
        {feedback ? (
          <section
            aria-live="polite"
            ref={feedbackPanel}
            className={`mt-5 rounded-3xl border p-5 sm:p-6 ${
              feedback.is_correct
                ? 'border-emerald-200 bg-emerald-50'
                : 'border-rose-200 bg-rose-50'
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className={`text-xl font-extrabold ${feedback.is_correct ? 'text-emerald-800' : 'text-rose-800'}`}>
                  {feedback.is_correct ? 'Correct' : 'Not quite'}
                </p>
                {!feedback.is_correct ? (
                  <p className="mt-1 text-sm font-semibold text-rose-700">Correct answer: {feedback.correct_answer_text}</p>
                ) : null}
              </div>
              <XpBadge xp={feedback.xp_earned} />
            </div>
            <div className="mt-5 border-t border-current/10 pt-4">
              <p className="text-xs font-bold uppercase tracking-[0.15em] text-slate-500">Rationale</p>
              <p className="mt-2 leading-7 text-slate-700">
                {feedback.rationale ?? 'A concise rationale is still under content review for this question.'}
              </p>
            </div>
          </section>
        ) : (
          <p className="mt-4 text-center text-sm font-semibold text-slate-400">Choose the best answer to continue.</p>
        )}
      </div>
      {feedback ? (
        <div className="fixed inset-x-0 bottom-0 z-50 border-t border-slate-200 bg-white/95 px-5 pb-[max(1rem,env(safe-area-inset-bottom))] pt-4 shadow-[0_-16px_40px_-24px_rgba(15,23,42,0.45)] backdrop-blur">
          <div className="mx-auto flex max-w-3xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <p className={`font-extrabold ${feedback.is_correct ? 'text-emerald-700' : 'text-rose-700'}`}>
                {feedback.is_correct ? 'Correct — nice work.' : 'Answer reviewed — keep going.'}
              </p>
              <p className="text-sm font-semibold text-slate-500">
                Question {currentIndex + 1} of {data.target_question_count}
              </p>
            </div>
            <button
              className="min-h-12 w-full rounded-2xl bg-ink px-7 font-extrabold text-white hover:bg-slate-800 disabled:opacity-60 sm:w-auto"
              disabled={completeSession.isPending}
              onClick={continuePractice}
              type="button"
            >
              {completeSession.isPending
                ? 'FINISHING…'
                : currentIndex === data.questions.length - 1
                  ? 'FINISH SESSION'
                  : 'CONTINUE'}
            </button>
          </div>
          {completeSession.isError ? (
            <div className="mx-auto mt-3 max-w-3xl">
              <ErrorNotice message={completeSession.error.message} />
            </div>
          ) : null}
        </div>
      ) : null}
    </main>
  )
}
