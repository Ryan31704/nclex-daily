import { Outlet } from 'react-router-dom'

import { BrandLogo } from './BrandLogo'
import { MobileNav } from './MobileNav'
import { Sidebar } from './Sidebar'

export function AppShell() {
  return (
    <div className="min-h-screen bg-canvas">
      <Sidebar />
      <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/90 px-4 pt-[env(safe-area-inset-top)] backdrop-blur lg:hidden">
        <div className="flex min-h-16 items-center">
          <BrandLogo />
        </div>
      </header>
      <main className="min-h-screen pb-[calc(6rem+env(safe-area-inset-bottom))] lg:ml-64 lg:pb-0">
        <Outlet />
      </main>
      <MobileNav />
    </div>
  )
}
