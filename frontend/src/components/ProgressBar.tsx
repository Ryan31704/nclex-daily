interface ProgressBarProps {
  value: number
  label: string
  showValue?: boolean
  size?: 'sm' | 'md'
}

export function ProgressBar({ value, label, showValue = false, size = 'md' }: ProgressBarProps) {
  const boundedValue = Math.max(0, Math.min(100, value))
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <span className={showValue ? 'text-sm font-semibold text-slate-500' : 'sr-only'}>
          {label}
        </span>
        {showValue ? (
          <span className="text-sm font-extrabold text-ink">{Math.round(boundedValue)}%</span>
        ) : null}
      </div>
      <div
        aria-label={label}
        aria-valuemax={100}
        aria-valuemin={0}
        aria-valuenow={Math.round(boundedValue)}
        className={`${showValue ? 'mt-2' : ''} overflow-hidden rounded-full bg-slate-100 ${
          size === 'sm' ? 'h-2' : 'h-3'
        }`}
        role="progressbar"
      >
        <div
          className="h-full rounded-full bg-gradient-to-r from-teal-500 to-sky-500 transition-[width] duration-500"
          style={{ width: `${boundedValue}%` }}
        />
      </div>
    </div>
  )
}
