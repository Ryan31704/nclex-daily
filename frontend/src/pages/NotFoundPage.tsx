import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-canvas px-5 text-center">
      <div>
        <p className="text-sm font-bold uppercase tracking-widest text-teal-700">404</p>
        <h1 className="mt-3 text-4xl font-bold text-ink">Page not found</h1>
        <Link
          className="mt-6 inline-flex rounded-xl bg-teal-600 px-5 py-3 font-semibold text-white hover:bg-teal-700"
          to="/"
        >
          Return home
        </Link>
      </div>
    </main>
  )
}
