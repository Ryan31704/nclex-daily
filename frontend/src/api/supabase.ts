import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY
const inviteSetupStorageKey = 'nclex-daily:invite-password-setup'
let persistentStorageRequest: Promise<boolean> | null = null

function isInviteCallback(): boolean {
  if (typeof window === 'undefined') {
    return false
  }

  const hashParams = new URLSearchParams(window.location.hash.slice(1))
  return hashParams.get('type') === 'invite'
}

if (isInviteCallback()) {
  window.sessionStorage.setItem(inviteSetupStorageKey, 'true')
}

export function isInviteSetupPending(): boolean {
  return (
    typeof window !== 'undefined' &&
    window.sessionStorage.getItem(inviteSetupStorageKey) === 'true'
  )
}

export function markInviteSetupPending(): void {
  if (typeof window !== 'undefined') {
    window.sessionStorage.setItem(inviteSetupStorageKey, 'true')
  }
}

export function clearInviteSetupPending(): void {
  if (typeof window !== 'undefined') {
    window.sessionStorage.removeItem(inviteSetupStorageKey)
  }
}

export function requestPersistentStorage(): Promise<boolean> {
  if (
    typeof navigator === 'undefined' ||
    !navigator.storage?.persisted ||
    !navigator.storage.persist
  ) {
    return Promise.resolve(false)
  }

  if (!persistentStorageRequest) {
    persistentStorageRequest = navigator.storage
      .persisted()
      .then((isPersistent) =>
        isPersistent ? true : navigator.storage.persist(),
      )
      .catch(() => false)
  }

  return persistentStorageRequest
}

export const allowSignups = import.meta.env.VITE_ALLOW_SIGNUPS !== 'false'

export const authConfigError =
  !supabaseUrl || !supabasePublishableKey
    ? 'Supabase is not configured. Add VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY to frontend/.env.'
    : null

export const supabase =
  supabaseUrl && supabasePublishableKey
    ? createClient(supabaseUrl, supabasePublishableKey, {
        auth: {
          autoRefreshToken: true,
          detectSessionInUrl: true,
          persistSession: true,
        },
      })
    : null
