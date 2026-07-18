import axios from 'axios'
import type { ApiResponse } from './types'
import { getAdminToken, getUserToken, getVisitorId } from '@/utils/auth'

const client = axios.create({
  baseURL: '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

client.interceptors.request.use((config) => {
  const adminToken = getAdminToken()
  const userToken = getUserToken()
  config.headers.set('X-Visitor-ID', getVisitorId())
  if (adminToken) config.headers.set('X-Admin-Token', adminToken)
  if (userToken) config.headers.set('X-User-Token', userToken)
  return config
})

client.interceptors.response.use(
  (response) => {
    const data = response.data as ApiResponse
    if (data.code !== undefined && data.code !== 0) {
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    return response
  },
  (error) => {
    const msg = error.response?.data?.detail || error.response?.data?.message || error.message || '网络错误'
    return Promise.reject(new Error(msg))
  },
)

export default client
