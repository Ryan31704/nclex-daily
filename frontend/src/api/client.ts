const apiUrl = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
)

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
}

export async function apiGet<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  let response: Response

  try {
    response = await fetch(`${apiUrl}${path}`, {
      headers: {
        Accept: 'application/json',
        ...(options.accessToken
          ? { Authorization: `Bearer ${options.accessToken}` }
          : {}),
      },
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
