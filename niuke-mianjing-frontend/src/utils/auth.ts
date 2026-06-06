const ADMIN_TOKEN_STORAGE = 'offerlens_admin_token'
const VISITOR_ID_STORAGE = 'offerlens_visitor_id'
export const ADMIN_TOKEN_CHANGED_EVENT = 'offerlens-admin-token-changed'

export const getAdminToken = () => sessionStorage.getItem(ADMIN_TOKEN_STORAGE) || ''

export const setAdminToken = (value: string) => {
  sessionStorage.setItem(ADMIN_TOKEN_STORAGE, value)
  window.dispatchEvent(new Event(ADMIN_TOKEN_CHANGED_EVENT))
}

export const clearAdminToken = () => {
  sessionStorage.removeItem(ADMIN_TOKEN_STORAGE)
  window.dispatchEvent(new Event(ADMIN_TOKEN_CHANGED_EVENT))
}

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
