const ADMIN_TOKEN_STORAGE = 'offerlens_admin_token'
const VISITOR_ID_STORAGE = 'offerlens_visitor_id'
const USER_SESSION_STORAGE = 'offerlens_user_session'
export const ADMIN_TOKEN_CHANGED_EVENT = 'offerlens-admin-token-changed'
export const USER_SESSION_CHANGED_EVENT = 'offerlens-user-session-changed'

export interface UserSession {
  id: number
  email: string
  display_name: string
  token: string
}

export const getAdminToken = () => sessionStorage.getItem(ADMIN_TOKEN_STORAGE) || ''

export const setAdminToken = (value: string) => {
  sessionStorage.setItem(ADMIN_TOKEN_STORAGE, value)
  window.dispatchEvent(new Event(ADMIN_TOKEN_CHANGED_EVENT))
}

export const clearAdminToken = () => {
  sessionStorage.removeItem(ADMIN_TOKEN_STORAGE)
  window.dispatchEvent(new Event(ADMIN_TOKEN_CHANGED_EVENT))
}

export const parseUserSession = (raw: string | null): UserSession | null => {
  if (!raw) return null
  try {
    const value = JSON.parse(raw)
    return Number.isInteger(value?.id) && value?.email && value?.token
      ? { ...value, display_name: value.display_name || value.email } as UserSession
      : null
  } catch {
    return null
  }
}

export const getUserSession = () => parseUserSession(localStorage.getItem(USER_SESSION_STORAGE))
export const getUserToken = () => getUserSession()?.token || ''

export const setUserSession = (session: UserSession) => {
  localStorage.setItem(USER_SESSION_STORAGE, JSON.stringify(session))
  window.dispatchEvent(new Event(USER_SESSION_CHANGED_EVENT))
}

export const clearUserSession = () => {
  localStorage.removeItem(USER_SESSION_STORAGE)
  window.dispatchEvent(new Event(USER_SESSION_CHANGED_EVENT))
}

export const isAnonymousPageAllowed = (page: number, token = getUserToken()) => page <= 2 || Boolean(token)
export const userLoginPath = (from: string) => `/login?from=${encodeURIComponent(from)}`

const createVisitorId = () => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }

  if (typeof crypto !== 'undefined' && typeof crypto.getRandomValues === 'function') {
    const bytes = crypto.getRandomValues(new Uint8Array(16))
    bytes[6] = (bytes[6] & 0x0f) | 0x40
    bytes[8] = (bytes[8] & 0x3f) | 0x80
    const value = Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')
    return `${value.slice(0, 8)}-${value.slice(8, 12)}-${value.slice(12, 16)}-${value.slice(16, 20)}-${value.slice(20)}`
  }

  return `visitor-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 12)}`
}

export const getVisitorId = () => {
  const saved = localStorage.getItem(VISITOR_ID_STORAGE)
  if (saved) return saved
  const id = createVisitorId()
  localStorage.setItem(VISITOR_ID_STORAGE, id)
  return id
}
