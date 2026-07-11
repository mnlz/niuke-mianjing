import type { RecruitmentInterview } from '@/api/types'

export const interviewRoute = (item: RecruitmentInterview) => {
  const params = new URLSearchParams({ record: String(item.id) })
  if (item.company) params.set('company', item.company)
  if (item.post) params.set('post', item.post)
  return `/interviews?${params.toString()}`
}
