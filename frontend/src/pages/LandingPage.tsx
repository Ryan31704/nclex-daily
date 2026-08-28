import { Link } from 'react-router-dom'

import { allowSignups } from '../api/supabase'

export function LandingPage() {
  return (
    <main className="relative isolate min-h-screen overflow-hidden bg-canvas px-5 py-6 sm:px-8">
      <div
        aria-hidden="true"
        className="absolute -right-32 -top-40 -z-10 h-96 w-96 rounded-full bg-teal-100 blur-3xl"
      />
      <div
        aria-hidden="true"
        className="absolute -bottom-44 -left-32 -z-10 h-96 w-96 rounded-full bg-orange-100 blur-3xl"
      />

      <header className="mx-auto flex max-w-6xl items-center justify-between">
        <Link className="text-xl font-extrabold tracking-tight text-ink" to="/">
          NCLEX <span className="text-teal-600">Daily</span>
        </Link>
        <Link
          className="rounded-xl px-4 py-2 font-semibold text-teal-700 hover:bg-white"
          to="/login"
        >
          Log In
        </Link>
      </header>

      <section className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-5xl items-center py-16">
        <div className="max-w-3xl">
          <span className="inline-flex rounded-full bg-white px-4 py-2 text-sm font-semibold text-teal-700 shadow-sm">
            Ten focused minutes a day
          </span>
          <h1 className="mt-7 text-5xl font-bold tracking-tight text-ink sm:text-7xl">
            Pass the NCLEX one day at a time.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-600 sm:text-xl">
            Build a consistent practice habit, understand every answer, and see
            exactly which nursing topics need your attention.
          </p>
          <div className="mt-9 flex flex-col gap-3 sm:flex-row">
            <Link
              className="inline-flex min-h-12 items-center justify-center rounded-2xl bg-teal-600 px-7 py-3 font-bold text-white shadow-lg shadow-teal-600/20 transition hover:bg-teal-700"
              to={allowSignups ? '/login?mode=signup' : '/login'}
            >
              {allowSignups ? 'Start Studying' : 'Private Beta Log In'}
            </Link>
            <Link
              className="inline-flex min-h-12 items-center justify-center rounded-2xl border border-slate-200 bg-white px-7 py-3 font-bold text-ink transition hover:border-teal-500"
              to="/login"
            >
              Log In
            </Link>
          </div>
        </div>
      </section>
    </main>
  )
}
