import { useEffect, useState } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'

interface InstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const INSTALL_DISMISSED_KEY = 'nclex-daily-install-dismissed'

function isIosDevice(): boolean {
  return /iphone|ipad|ipod/i.test(navigator.userAgent)
}

function isStandalone(): boolean {
  return window.matchMedia('(display-mode: standalone)').matches
    || Boolean((navigator as Navigator & { standalone?: boolean }).standalone)
}

export function PwaStatus() {
  const [isOnline, setIsOnline] = useState(() => navigator.onLine)
  const [installPrompt, setInstallPrompt] = useState<InstallPromptEvent | null>(null)
  const [installDismissed, setInstallDismissed] = useState(
    () => sessionStorage.getItem(INSTALL_DISMISSED_KEY) === 'true',
  )
  const [showIosInstructions, setShowIosInstructions] = useState(
    () => isIosDevice() && !isStandalone(),
  )
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    offlineReady: [offlineReady, setOfflineReady],
    updateServiceWorker,
  } = useRegisterSW()

  useEffect(() => {
    const handleOnline = () => setIsOnline(true)
    const handleOffline = () => setIsOnline(false)
    const handleInstallPrompt = (event: Event) => {
      event.preventDefault()
      setInstallPrompt(event as InstallPromptEvent)
    }
    const handleInstalled = () => {
      setInstallPrompt(null)
      setShowIosInstructions(false)
    }

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    window.addEventListener('beforeinstallprompt', handleInstallPrompt)
    window.addEventListener('appinstalled', handleInstalled)
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
      window.removeEventListener('beforeinstallprompt', handleInstallPrompt)
      window.removeEventListener('appinstalled', handleInstalled)
    }
  }, [])

  useEffect(() => {
    if (!offlineReady) return
    const timeoutId = window.setTimeout(() => setOfflineReady(false), 5000)
    return () => window.clearTimeout(timeoutId)
  }, [offlineReady, setOfflineReady])

  const dismissInstall = () => {
    sessionStorage.setItem(INSTALL_DISMISSED_KEY, 'true')
    setInstallDismissed(true)
  }

  const installApp = async () => {
    if (!installPrompt) return
    await installPrompt.prompt()
    const choice = await installPrompt.userChoice
    if (choice.outcome === 'accepted') {
      setInstallPrompt(null)
    }
  }

  const shouldOfferInstall = !installDismissed
    && !isStandalone()
    && (Boolean(installPrompt) || showIosInstructions)

  return (
    <>
      {!isOnline ? (
        <div
          className="fixed inset-x-3 top-[max(0.75rem,env(safe-area-inset-top))] z-[70] mx-auto max-w-sm rounded-2xl bg-amber-950 px-4 py-3 text-center text-sm font-bold text-white shadow-xl"
          role="status"
        >
          You’re offline. Reconnect to load questions and save answers.
        </div>
      ) : null}

      {shouldOfferInstall ? (
        <aside className="fixed inset-x-3 bottom-[calc(6rem+env(safe-area-inset-bottom))] z-[60] mx-auto max-w-md rounded-3xl border border-teal-200 bg-white p-4 shadow-2xl lg:bottom-5 lg:right-5 lg:left-auto">
          <div className="flex items-start gap-3">
            <img
              alt=""
              className="h-12 w-12 rounded-2xl"
              height="48"
              src="/pwa-192x192.png"
              width="48"
            />
            <div className="min-w-0 flex-1">
              <p className="font-extrabold text-ink">Install NCLEX Daily</p>
              <p className="mt-1 text-sm leading-5 text-slate-500">
                {installPrompt
                  ? 'Add it to your home screen for a focused, full-screen experience.'
                  : 'On iPhone or iPad, tap Share, then Add to Home Screen. Sign in once from the installed app.'}
              </p>
            </div>
          </div>
          <div className="mt-3 flex justify-end gap-2">
            <button
              className="min-h-11 rounded-xl px-4 text-sm font-bold text-slate-500"
              onClick={dismissInstall}
              type="button"
            >
              Not now
            </button>
            {installPrompt ? (
              <button
                className="min-h-11 rounded-xl bg-teal-600 px-5 text-sm font-extrabold text-white"
                onClick={() => void installApp()}
                type="button"
              >
                Install app
              </button>
            ) : null}
          </div>
        </aside>
      ) : null}

      {needRefresh ? (
        <aside className="fixed inset-x-3 bottom-[calc(6rem+env(safe-area-inset-bottom))] z-[65] mx-auto max-w-md rounded-3xl bg-ink p-4 text-white shadow-2xl lg:bottom-5 lg:right-5 lg:left-auto">
          <p className="font-extrabold">An update is ready</p>
          <p className="mt-1 text-sm text-slate-300">Refresh to use the newest version.</p>
          <div className="mt-3 flex justify-end gap-2">
            <button
              className="min-h-11 rounded-xl px-4 text-sm font-bold text-slate-300"
              onClick={() => setNeedRefresh(false)}
              type="button"
            >
              Later
            </button>
            <button
              className="min-h-11 rounded-xl bg-teal-500 px-5 text-sm font-extrabold text-white"
              onClick={() => void updateServiceWorker(true)}
              type="button"
            >
              Refresh
            </button>
          </div>
        </aside>
      ) : null}

      {offlineReady && !needRefresh ? (
        <div
          className="fixed bottom-[calc(6rem+env(safe-area-inset-bottom))] left-1/2 z-[55] -translate-x-1/2 rounded-full bg-ink px-4 py-2 text-sm font-bold text-white shadow-xl lg:bottom-5"
          role="status"
        >
          App ready for offline launch
        </div>
      ) : null}
    </>
  )
}
