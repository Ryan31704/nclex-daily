import type { TopicGroup, TopicProgress } from '../types/practice'

export interface CategoryProgress {
  id: string
  name: string
  slug: string
  masteryScore: number
  attemptedQuestions: number
  totalQuestions: number
  classification: TopicProgress['classification']
}

export function classificationFor(score: number): TopicProgress['classification'] {
  if (score < 40) return 'weak'
  if (score < 70) return 'developing'
  if (score < 100) return 'strong'
  return 'mastered'
}

export function buildCategoryProgress(
  groups: TopicGroup[],
  progressItems: TopicProgress[],
): CategoryProgress[] {
  const progressByTopic = new Map(
    progressItems.map((item) => [item.topic.id, item] as const),
  )

  return groups.map((group) => {
    let attemptedQuestions = 0
    let demonstratedQuestions = 0
    for (const child of group.children) {
      const progress = progressByTopic.get(child.id)
      if (progress) {
        attemptedQuestions += progress.attempted_questions
        demonstratedQuestions += (progress.mastery_score / 100) * child.question_count
      }
    }
    const masteryScore = group.question_count
      ? Math.round((demonstratedQuestions / group.question_count) * 1000) / 10
      : 0
    return {
      id: group.id,
      name: group.name,
      slug: group.slug,
      masteryScore,
      attemptedQuestions,
      totalQuestions: group.question_count,
      classification: classificationFor(masteryScore),
    }
  })
}

export function formatRelativeDate(value: string | null): string {
  if (!value) return 'Not practiced yet'
  const date = new Date(value)
  const elapsedDays = Math.floor((Date.now() - date.getTime()) / 86_400_000)
  if (elapsedDays <= 0) return 'Today'
  if (elapsedDays === 1) return 'Yesterday'
  if (elapsedDays < 7) return `${elapsedDays} days ago`
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
  }).format(date)
}
