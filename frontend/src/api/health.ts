import { apiGet } from './client'

export interface HealthResponse {
  status: 'ok'
  service: string
  environment: string
}

export function getHealth(): Promise<HealthResponse> {
  return apiGet<HealthResponse>('/api/v1/health')
}
