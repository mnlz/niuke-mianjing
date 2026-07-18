import client from './client'
import type { ApiResponse } from './types'

export const authApi = {
  login: (apiKey: string) =>
    client
      .post<ApiResponse<{ authenticated: boolean; token: string }>>('/api/auth/login', { api_key: apiKey })
      .then((response) => response.data.data),

  me: () =>
    client.get<ApiResponse<{ authenticated: boolean }>>('/api/auth/me').then((response) => response.data.data),

  userRegister: (email: string, password: string) =>
    client.post<ApiResponse<{ id: number; email: string; display_name: string; token: string }>>('/api/user-auth/register', { email, password }).then((response) => response.data.data),

  userLogin: (email: string, password: string) =>
    client.post<ApiResponse<{ id: number; email: string; display_name: string; token: string }>>('/api/user-auth/login', { email, password }).then((response) => response.data.data),

  userMe: () =>
    client.get<ApiResponse<{ id: number; email: string; display_name: string }>>('/api/user-auth/me').then((response) => response.data.data),
}
