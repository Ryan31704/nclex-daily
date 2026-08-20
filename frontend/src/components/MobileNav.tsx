import { NavLink } from 'react-router-dom'

import { AppIcon } from './AppIcon'

const navigation = [
  { label: 'Home', to: '/dashboard', icon: 'home' },
  { label: 'Progress', to: '/progress', icon: 'progress' },
  { label: 'Practice', to: '/practice', icon: 'practice' },
  { label: 'Review', to: '/review', icon: 'review' },
  { label: 'Profile', to: '/profile', icon: 'profile' },
] as const

export function MobileNav() {
  return (
    <nav
      aria-label="Mobile navigation"
      className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-5 border-t border-slate-200 bg-white/95 px-1 pb-[max(0.5rem,env(safe-area-inset-bottom))] pt-1.5 shadow-[0_-12px_32px_-24px_rgba(15,23,42,0.45)] backdrop-blur lg:hidden"
    >
      {navigation.map((item) => (
        <NavLink
          key={item.to}
          className={({ isActive }) =>
            `relative flex min-h-14 flex-col items-center justify-center gap-1 rounded-xl text-[0.65rem] font-bold transition ${
              isActive ? 'bg-teal-50 text-teal-700' : 'text-slate-500'
            }`
          }
          end={item.to === '/dashboard'}
          to={item.to}
        >
          <AppIcon className="h-[1.15rem] w-[1.15rem]" name={item.icon} />
          {item.label}
        </NavLink>
      ))}
    </nav>
  )
}
