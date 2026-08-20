interface XpBadgeProps {
  xp: number
}

export function XpBadge({ xp }: XpBadgeProps) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full bg-amber-50 px-3 py-1.5 text-sm font-bold text-amber-700">
      <span aria-hidden="true">★</span>
      {xp} XP
    </span>
  )
}
