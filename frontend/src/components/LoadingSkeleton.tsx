interface LoadingSkeletonProps {
  rows?: number
}

export function LoadingSkeleton({ rows = 3 }: LoadingSkeletonProps) {
  return (
    <div aria-busy="true" aria-label="Loading content" className="space-y-4" role="status">
      {Array.from({ length: rows }, (_, index) => (
        <div
          key={index}
          className="h-32 animate-pulse rounded-3xl border border-slate-100 bg-slate-100"
        />
      ))}
      <span className="sr-only">Loading…</span>
    </div>
  )
}
