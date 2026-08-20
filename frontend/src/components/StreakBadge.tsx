interface StreakBadgeProps {
  days: number
}

export function StreakBadge({ days }: StreakBadgeProps) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-orange-50 px-3 py-1.5 text-sm font-bold text-orange-700">
      <span aria-hidden="true">🔥</span>
      {days} day streak
    </span>
  )
}
