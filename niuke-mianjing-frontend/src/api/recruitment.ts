import client from './client'
import type { ApiResponse, RecruitmentJobPage, RecruitmentSource, RecruitmentTrack } from './types'

export const recruitmentApi = {
  sources: () =>
    client.get<ApiResponse<RecruitmentSource[]>>('/api/recruitment/sources').then((r) => r.data.data),

  tracks: () =>
    client.get<ApiResponse<RecruitmentTrack[]>>('/api/recruitment/tracks').then((r) => r.data.data),

  jobs: (params: { source: string; keyword?: string; track?: string; page?: number; page_size?: number }) =>
    client.get<ApiResponse<RecruitmentJobPage>>('/api/recruitment/jobs', { params, timeout: 60000 }).then((r) => r.data.data),
}
