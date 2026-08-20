import type { ReactNode } from 'react'

interface PageHeaderProps {
  eyebrow?: string
  title: string
  description?: string
  action?: ReactNode
  inverted?: boolean
}

export function PageHeader({ eyebrow, title, description, action, inverted = false }: PageHeaderProps) {
  return (
    <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div>
        {eyebrow ? (
          <p className={`text-xs font-bold uppercase tracking-[0.18em] ${inverted ? 'text-teal-100' : 'text-teal-700'}`}>
            {eyebrow}
          </p>
        ) : null}
        <h1 className={`mt-2 break-words text-[1.75rem] font-extrabold leading-tight tracking-tight sm:text-4xl ${inverted ? 'text-white' : 'text-ink'}`}>
          {title}
        </h1>
        {description ? (
          <p className={`mt-2 max-w-2xl leading-7 ${inverted ? 'text-slate-300' : 'text-slate-500'}`}>{description}</p>
        ) : null}
      </div>
      {action ? <div className="w-full sm:w-auto">{action}</div> : null}
    </header>
  )
}
