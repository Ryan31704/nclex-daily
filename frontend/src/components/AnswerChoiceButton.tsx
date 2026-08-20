interface AnswerChoiceButtonProps {
  letter: string
  text: string
  state: 'idle' | 'selected' | 'correct' | 'incorrect' | 'muted'
  disabled: boolean
  onSelect: () => void
}

const stateClasses = {
  idle: 'border-slate-200 bg-white hover:border-teal-400 hover:bg-teal-50/40',
  selected: 'border-teal-600 bg-teal-50 ring-4 ring-teal-100',
  correct: 'border-emerald-500 bg-emerald-50 ring-4 ring-emerald-100',
  incorrect: 'border-rose-400 bg-rose-50 ring-4 ring-rose-100',
  muted: 'border-slate-200 bg-slate-50 opacity-65',
}

export function AnswerChoiceButton({
  letter,
  text,
  state,
  disabled,
  onSelect,
}: AnswerChoiceButtonProps) {
  return (
    <button
      aria-pressed={state === 'selected'}
      className={`flex min-h-16 w-full items-center gap-4 rounded-2xl border-2 p-3 text-left font-semibold text-ink transition sm:p-4 ${stateClasses[state]}`}
      disabled={disabled}
      onClick={onSelect}
      type="button"
    >
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-current/15 bg-white text-sm font-extrabold">
        {letter}
      </span>
      <span className="min-w-0 flex-1 leading-6">{text}</span>
      {state === 'correct' ? <span className="ml-auto hidden shrink-0 font-extrabold text-emerald-700 sm:inline">Correct</span> : null}
      {state === 'incorrect' ? <span className="ml-auto hidden shrink-0 font-extrabold text-rose-700 sm:inline">Your answer</span> : null}
    </button>
  )
}
