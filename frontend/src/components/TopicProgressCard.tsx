import { Link } from 'react-router-dom'

import type { CategoryProgress } from '../utils/progress'
import { AppIcon } from './AppIcon'
import { ProgressBar } from './ProgressBar'

interface TopicProgressCardProps {
  category: CategoryProgress
}

const labels = {
  weak: 'Needs focus',
  developing: 'Developing',
  strong: 'Strong',
  mastered: 'Mastered',
}

export function TopicProgressCard({ category }: TopicProgressCardProps) {
  return (
    <Link
      className="group block rounded-3xl border border-slate-200 bg-white p-5 shadow-card transition hover:-translate-y-0.5 hover:border-teal-300"
      to={`/topics/${category.slug}`}
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.15em] text-teal-700">
            {labels[category.classification]}
          </p>
          <h3 className="mt-2 text-lg font-extrabold leading-snug text-ink">
            {category.name}
          </h3>
        </div>
        <span className="rounded-full bg-slate-50 p-2 text-slate-400 transition group-hover:bg-teal-50 group-hover:text-teal-700">
          <AppIcon name="arrow" />
        </span>
      </div>
      <div className="mt-5">
        <ProgressBar
          label={`${category.name} mastery`}
          showValue
          size="sm"
          value={category.masteryScore}
        />
      </div>
      <p className="mt-3 text-sm text-slate-500">
        {category.attemptedQuestions} attempts · {category.totalQuestions} questions available
      </p>
    </Link>
  )
}
