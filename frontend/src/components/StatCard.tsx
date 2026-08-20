import type { ReactNode } from 'react'

interface StatCardProps {
  label: string
  value: string
  detail?: string
  icon: ReactNode
  tone?: 'teal' | 'coral' | 'gold' | 'blue'
}

const tones = {
  teal: 'bg-teal-50 text-teal-700',
  coral: 'bg-rose-50 text-rose-700',
  gold: 'bg-amber-50 text-amber-700',
  blue: 'bg-sky-50 text-sky-700',
}

export function StatCard({ label, value, detail, icon, tone = 'teal' }: StatCardProps) {
  return (
    <article className="rounded-3xl border border-slate-200 bg-white p-5 shadow-card">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-extrabold tracking-tight text-ink">{value}</p>
          {detail ? <p className="mt-1 text-xs font-medium text-slate-400">{detail}</p> : null}
        </div>
        <span className={`grid h-11 w-11 place-items-center rounded-2xl text-xl ${tones[tone]}`}>
          {icon}
        </span>
      </div>
    </article>
  )
}
