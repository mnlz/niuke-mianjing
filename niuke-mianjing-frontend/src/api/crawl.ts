import client from './client'
import type { ApiResponse, ExportMdRequest, JobPostItem, JobTreeItem, QuickCrawlRequest } from './types'

export const quickCrawlApi = {
  getPosts: () =>
    client.get<ApiResponse<{ posts: JobPostItem[]; tree: JobTreeItem[] }>>('/api/crawl/posts').then((r) => r.data.data),

  start: (data: QuickCrawlRequest) =>
    client.post<ApiResponse<null>>('/api/crawl/quick', data).then((r) => r.data),

  exportMd: (data: ExportMdRequest) =>
    client
      .post('/api/crawl/export-md', data, { responseType: 'blob' })
      .then((r) => {
        const blob = new Blob([r.data], { type: 'text/markdown;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        const parts: string[] = []
        if (data.post) parts.push(data.post)
        if (data.company) parts.push(data.company)
        if (data.group_by) parts.push(data.group_by === 'company' ? '按公司分组' : '按方向分组')
        const suffix = parts.length > 0 ? `_${parts.join('_')}` : ''
        a.download = `面经数据${suffix}_${new Date().toISOString().slice(0, 10)}.md`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
        return true
      }),
}
