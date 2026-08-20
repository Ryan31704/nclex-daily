import type { ReactNode } from 'react'

interface QuestionCardProps {
  topic: string
  question: string
  children: ReactNode
}

export function QuestionCard({ topic, question, children }: QuestionCardProps) {
  return (
    <article className="rounded-[2rem] border border-slate-200 bg-white p-5 shadow-card sm:p-8">
      <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-700">{topic}</p>
      <h1 className="mt-4 text-2xl font-extrabold leading-snug tracking-tight text-ink sm:text-3xl">
        {question}
      </h1>
      <div className="mt-7 space-y-3">{children}</div>
    </article>
  )
}
