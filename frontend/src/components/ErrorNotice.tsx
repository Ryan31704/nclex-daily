interface ErrorNoticeProps {
  message: string
  onRetry?: () => void
}

export function ErrorNotice({ message, onRetry }: ErrorNoticeProps) {
  return (
    <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-900" role="alert">
      <p className="font-bold">Something went wrong</p>
      <p className="mt-1 text-sm">{message}</p>
      {onRetry ? (
        <button
          className="mt-3 rounded-xl bg-white px-4 py-2 text-sm font-bold text-rose-800 shadow-sm"
          onClick={onRetry}
          type="button"
        >
          Try again
        </button>
      ) : null}
    </div>
  )
}
