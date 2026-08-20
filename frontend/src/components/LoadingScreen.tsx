export function LoadingScreen() {
  return (
    <main
      aria-busy="true"
      aria-label="Loading authentication status"
      className="grid min-h-screen place-items-center bg-canvas"
    >
      <div className="text-center" role="status">
        <div
          aria-hidden="true"
          className="mx-auto h-11 w-11 animate-spin rounded-full border-4 border-teal-100 border-t-teal-600"
        />
        <p className="mt-4 font-medium text-slate-600">Preparing your study space…</p>
      </div>
    </main>
  )
}
