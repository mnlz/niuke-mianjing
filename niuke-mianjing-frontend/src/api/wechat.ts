import client from './client'
import type {
  ApiResponse,
  WeChatAIGenerateRequest,
  WeChatAISaveRequest,
  WeChatArticleData,
  WeChatDraftData,
  WeChatDraftRequest,
  WeChatPreviewData,
  WeChatPreviewRequest,
} from './types'

export const wechatApi = {
  preview: (data: WeChatPreviewRequest) =>
    client.post<ApiResponse<WeChatPreviewData>>('/api/wechat/preview', data).then((r) => r.data.data),

  createDraft: (data: WeChatDraftRequest) =>
    client.post<ApiResponse<WeChatDraftData>>('/api/wechat/draft', data, { timeout: 120000 }).then((r) => r.data.data),

  aiGenerate: (data: WeChatAIGenerateRequest) =>
    client
      .post<ApiResponse<WeChatArticleData>>('/api/wechat/ai-generate', data, { timeout: 240000 })
      .then((r) => r.data.data),

  saveGenerated: (data: WeChatAISaveRequest) =>
    client.post<ApiResponse<WeChatArticleData>>('/api/wechat/ai-save', data, { timeout: 180000 }).then((r) => r.data.data),

  article: (id: number) =>
    client.get<ApiResponse<WeChatArticleData>>(`/api/wechat/articles/${id}`).then((r) => r.data.data),

  publishSaved: (id: number) =>
    client
      .post<ApiResponse<WeChatDraftData>>(`/api/wechat/articles/${id}/draft`, undefined, { timeout: 120000 })
      .then((r) => r.data.data),
}
