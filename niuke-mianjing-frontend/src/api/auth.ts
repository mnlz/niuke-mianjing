import client from './client'
import type { ApiResponse } from './types'

export const authApi = {
  login: (apiKey: string) =>
    client
      .post<ApiResponse<{ authenticated: boolean; token: string }>>('/api/auth/login', { api_key: apiKey })
      .then((response) => response.data.data),

  me: () =>
    client.get<ApiResponse<{ authenticated: boolean }>>('/api/auth/me').then((response) => response.data.data),
}
