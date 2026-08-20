import { apiGet } from './client'

export interface Profile {
  id: string
  auth_user_id: string
  email: string | null
  display_name: string
  created_at: string
  current_streak: number
  longest_streak: number
  total_xp: number
  last_practice_date: string | null
}

export function getMyProfile(
  accessToken: string,
  signal?: AbortSignal,
): Promise<Profile> {
  return apiGet<Profile>('/api/v1/me', { accessToken, signal })
}
