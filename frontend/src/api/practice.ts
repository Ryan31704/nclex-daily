import { apiGet, apiPost } from './client'
import type {
  CompleteSessionResponse,
  DashboardData,
  MissedQuestion,
  PracticeSession,
  ProgressResponse,
  SubmitAnswerResponse,
  TopicGroup,
  TopicProgress,
} from '../types/practice'

export function getDashboard(accessToken: string, signal?: AbortSignal) {
  return apiGet<DashboardData>('/api/v1/dashboard', { accessToken, signal })
}

export function getTopics(accessToken: string, signal?: AbortSignal) {
  return apiGet<TopicGroup[]>('/api/v1/topics', { accessToken, signal })
}

export function getProgress(accessToken: string, signal?: AbortSignal) {
  return apiGet<ProgressResponse>('/api/v1/progress', { accessToken, signal })
}

export function getTopicProgress(
  accessToken: string,
  topicId: string,
  signal?: AbortSignal,
) {
  return apiGet<TopicProgress>(`/api/v1/topics/${topicId}/progress`, {
    accessToken,
    signal,
  })
}

export function startDailyPractice(accessToken: string, targetQuestionCount = 10) {
  return apiPost<PracticeSession>(
    '/api/v1/practice/daily/start',
    { target_question_count: targetQuestionCount },
    { accessToken },
  )
}

export function startQuickReview(accessToken: string) {
  return apiPost<PracticeSession>(
    '/api/v1/practice/quick-review/start',
    {},
    { accessToken },
  )
}

export function startRandomTest(accessToken: string, targetQuestionCount: number) {
  return apiPost<PracticeSession>(
    '/api/v1/practice/random/start',
    { target_question_count: targetQuestionCount },
    { accessToken },
  )
}

export function startTopicPractice(
  accessToken: string,
  topicId: string,
  targetQuestionCount = 10,
) {
  return apiPost<PracticeSession>(
    `/api/v1/practice/topic/${topicId}/start`,
    { target_question_count: targetQuestionCount },
    { accessToken },
  )
}

export function startMissedQuestionReview(
  accessToken: string,
  questionId: string,
) {
  return apiPost<PracticeSession>(
    `/api/v1/practice/review/${questionId}/start`,
    {},
    { accessToken },
  )
}

export function getPracticeSession(
  accessToken: string,
  sessionId: string,
  signal?: AbortSignal,
) {
  return apiGet<PracticeSession>(`/api/v1/practice/sessions/${sessionId}`, {
    accessToken,
    signal,
  })
}

export function submitPracticeAnswer(
  accessToken: string,
  sessionId: string,
  questionId: string,
  answer: unknown,
  responseTimeMs: number,
) {
  return apiPost<SubmitAnswerResponse>(
    `/api/v1/practice/sessions/${sessionId}/answer`,
    {
      question_id: questionId,
      answer,
      response_time_ms: responseTimeMs,
    },
    { accessToken },
  )
}

export function completePracticeSession(accessToken: string, sessionId: string) {
  return apiPost<CompleteSessionResponse>(
    `/api/v1/practice/sessions/${sessionId}/complete`,
    {},
    { accessToken },
  )
}

export function getMissedQuestions(
  accessToken: string,
  topicId: string | null,
  signal?: AbortSignal,
) {
  const search = topicId ? `?topic_id=${encodeURIComponent(topicId)}` : ''
  return apiGet<MissedQuestion[]>(`/api/v1/review/missed${search}`, {
    accessToken,
    signal,
  })
}
