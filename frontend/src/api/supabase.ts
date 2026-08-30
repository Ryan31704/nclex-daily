import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabasePublishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY
const inviteSetupStorageKey = 'nclex-daily:invite-password-setup'

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
