import { NavLink } from 'react-router-dom'

import { AppIcon } from './AppIcon'
import { BrandLogo } from './BrandLogo'

const navigation = [
  { label: 'Home', to: '/dashboard', icon: 'home' },
  { label: 'Progress', to: '/progress', icon: 'progress' },
  { label: 'Practice', to: '/practice', icon: 'practice' },
  { label: 'Review', to: '/review', icon: 'review' },
  { label: 'Profile', to: '/profile', icon: 'profile' },
] as const

export function Sidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-slate-200 bg-white px-5 py-7 lg:flex lg:flex-col">
      <BrandLogo />
      <nav aria-label="Primary navigation" className="mt-12 space-y-2">
        {navigation.map((item) => (
          <NavLink
            key={item.to}
            className={({ isActive }) =>
              `flex min-h-12 items-center gap-3 rounded-2xl px-4 font-bold transition ${
                isActive
                  ? 'bg-teal-50 text-teal-700'
                  : 'text-slate-500 hover:bg-slate-50 hover:text-ink'
              }`
            }
            end={item.to === '/dashboard'}
            to={item.to}
          >
            <AppIcon name={item.icon} />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto rounded-3xl bg-ink p-5 text-white">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-teal-100">
          Daily reminder
        </p>
        <p className="mt-3 text-sm font-semibold leading-6 text-slate-200">
          Ten focused minutes today can make tomorrow&apos;s questions feel easier.
        </p>
      </div>
    </aside>
  )
}
