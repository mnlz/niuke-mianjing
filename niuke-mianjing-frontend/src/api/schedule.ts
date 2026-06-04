import client from './client'
import type { ApiResponse, ScheduleJob, CreateScheduleRequest } from './types'

export const scheduleApi = {
  list: () =>
    client.get<ApiResponse<ScheduleJob[]>>('/api/schedule/list').then((r) => r.data.data),

  create: (data: CreateScheduleRequest) => {
    const payload =
      data.schedule_type === 'cron'
        ? { posts: data.posts, cron: data.schedule, max_pages: data.max_pages }
        : {
            posts: data.posts,
            interval_hours: Number(data.schedule.match(/(\d+)\s*h/)?.[1] || 0),
            interval_minutes: Number(data.schedule.match(/(\d+)\s*m/)?.[1] || data.schedule.match(/^(\d+)$/)?.[1] || 0),
            max_pages: data.max_pages,
          }
    return client.post<ApiResponse<ScheduleJob>>('/api/schedule', payload).then((r) => r.data.data)
  },

  delete: (jobId: string) =>
    client.delete<ApiResponse<null>>(`/api/schedule/${jobId}`).then((r) => r.data.data),

  pause: (jobId: string) =>
    client.post<ApiResponse<null>>(`/api/schedule/${jobId}/pause`).then((r) => r.data.data),

  resume: (jobId: string) =>
    client.post<ApiResponse<null>>(`/api/schedule/${jobId}/resume`).then((r) => r.data.data),
}
