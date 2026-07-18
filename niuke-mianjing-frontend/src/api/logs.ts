import client from './client'
import type { ApiResponse, CrawlLog, StatsData, NiukeRecord, NiukeDataResponse, CrawlRequest, FilterOptions } from './types'

export const logApi = {
  stats: () =>
    client.get<ApiResponse<StatsData>>('/api/logs/stats').then((r) => r.data.data),

  logs: (params?: { post?: string; status?: string; start_date?: string; end_date?: string; limit?: number }) =>
    client.get<ApiResponse<CrawlLog[]>>('/api/logs/crawl', { params }).then((r) => r.data.data),

  records: (params?: { post?: string; company?: string; role_group?: string; role_family?: string; limit?: number; offset?: number }) =>
    client.get<ApiResponse<NiukeDataResponse>>('/api/logs/data', { params }).then((r) => r.data.data),

  record: (id: number) =>
    client.get<ApiResponse<NiukeRecord>>(`/api/logs/data/${id}`).then((r) => r.data.data),

  filters: (params?: { company?: string }) =>
    client.get<ApiResponse<FilterOptions>>('/api/logs/filters', { params }).then((r) => r.data.data),
}

export const crawlApi = {
  start: (data: CrawlRequest) =>
    client.post<ApiResponse<null>>('/api/crawl/start', data).then((r) => r.data.data),

  stop: () =>
    client.post<ApiResponse<null>>('/api/crawl/stop').then((r) => r.data.data),

  status: () =>
    client.get<ApiResponse<unknown>>('/api/crawl/status').then((r) => r.data.data),
}
