import client from './client'
import type { ApiResponse, ReviewAIResult, ReviewMastery, ReviewOverview, ReviewProgress } from './types'

export const reviewApi = {
  progress: (recordIds: number[]) =>
    client
      .get<ApiResponse<ReviewProgress[]>>('/api/review/progress', {
        params: { record_ids: recordIds.join(',') },
      })
      .then((r) => r.data.data),

  updateProgress: (recordId: number, data: { favorite?: boolean; mastery?: ReviewMastery; note?: string | null }) =>
    client.put<ApiResponse<ReviewProgress>>(`/api/review/progress/${recordId}`, data).then((r) => r.data.data),

  overview: (params: { company: string; post: string; days?: number; limit?: number }) =>
    client.get<ApiResponse<ReviewOverview>>('/api/review/overview', { params }).then((r) => r.data.data),

  aiReview: (recordId: number, refresh = false) =>
    client
      .post<ApiResponse<ReviewAIResult>>(`/api/review/records/${recordId}/ai-review`, null, {
        params: { refresh },
        timeout: 90000,
      })
      .then((r) => r.data.data),
}
