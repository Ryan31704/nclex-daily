const apiUrl = (import.meta.env.VITE_API_URL ?? '').trim().replace(/\/$/, '')

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

interface ApiRequestOptions {
  accessToken?: string
  signal?: AbortSignal
  method?: 'GET' | 'POST'
  body?: unknown
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  let response: Response

  try {
    response = await fetch(`${apiUrl}${path}`, {
      method: options.method ?? 'GET',
      headers: {
        Accept: 'application/json',
        ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(options.accessToken
          ? { Authorization: `Bearer ${options.accessToken}` }
          : {}),
      },
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    })
  } catch {
    throw new ApiError('Unable to reach the API. Is the backend running?')
  }

  if (!response.ok) {
    let message = 'The API returned an unexpected response.'
    try {
      const body = (await response.json()) as { detail?: unknown }
      if (typeof body.detail === 'string') {
        message = body.detail
      }
    } catch {
      // Keep the safe fallback when an upstream response is not JSON.
    }
    throw new ApiError(message, response.status)
  }

  return response.json() as Promise<T>
}

export function apiGet<T>(
  path: string,
  options: Omit<ApiRequestOptions, 'method' | 'body'> = {},
): Promise<T> {
  return apiRequest<T>(path, options)
}

export function apiPost<T>(
  path: string,
  body: unknown,
  options: Omit<ApiRequestOptions, 'method' | 'body'> = {},
): Promise<T> {
  return apiRequest<T>(path, { ...options, method: 'POST', body })
}
