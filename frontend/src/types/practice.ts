export interface TopicReference {
  id: string
  name: string
  slug: string
}

export interface AnswerChoice {
  id: string
  choice_text: string
  display_order: number
}

export interface PracticeQuestion {
  id: string
  question_text: string
  question_type: string
  topic: TopicReference
  choices: AnswerChoice[]
  interaction: Record<string, unknown> | null
  case_study_markdown: string | null
}

export interface SessionQuestion {
  display_order: number
  answered: boolean
  question: PracticeQuestion
}

export interface PracticeSession {
  id: string
  practice_type: 'daily' | 'topic' | 'quick_review' | 'random'
  topic_id: string | null
  status: 'active' | 'completed' | 'abandoned'
  started_at: string
  completed_at: string | null
  target_question_count: number
  questions_completed: number
  correct_count: number
  xp_earned: number
  questions: SessionQuestion[]
}

export interface SubmitAnswerResponse {
  is_correct: boolean
  correct_answer: {
    id: string
    choice_text: string
  } | null
  correct_response: unknown
  correct_answer_text: string
  rationale: string | null
  xp_earned: number
  updated_topic_mastery: number
  mastery_classification: string
  questions_completed: number
  target_question_count: number
}

export interface CompleteSessionResponse {
  session_id: string
  status: string
  correct_count: number
  question_count: number
  xp_earned: number
  completion_bonus_xp: number
  total_xp: number
  current_streak: number
  longest_streak: number
  completed_at: string
}

export interface TopicProgress {
  topic: TopicReference
  attempted_questions: number
  correct_questions: number
  correct_percentage: number
  mastery_score: number
  classification: 'weak' | 'developing' | 'strong' | 'mastered'
  last_practiced_at: string | null
}

export interface ProgressResponse {
  overall_mastery: number
  questions_answered: number
  correct_questions: number
  topics: TopicProgress[]
}

export interface TopicChild {
  id: string
  name: string
  slug: string
  description: string | null
  display_order: number
  question_count: number
}

export interface TopicGroup {
  id: string
  name: string
  slug: string
  description: string | null
  display_order: number
  question_count: number
  children: TopicChild[]
}

export interface DashboardData {
  display_name: string
  current_streak: number
  longest_streak: number
  total_xp: number
  questions_answered: number
  overall_mastery: number
  daily_session: PracticeSession | null
  weakest_topics: TopicProgress[]
}

export interface MissedQuestion {
  attempt_id: string
  attempted_at: string
  selected_answer_id: string
  question: PracticeQuestion
}
