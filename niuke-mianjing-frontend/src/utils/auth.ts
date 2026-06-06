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

export const getVisitorId = () => {
  const saved = localStorage.getItem(VISITOR_ID_STORAGE)
  if (saved) return saved
  const id = crypto.randomUUID()
  localStorage.setItem(VISITOR_ID_STORAGE, id)
  return id
}
