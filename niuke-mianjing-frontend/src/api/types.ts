export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
  timestamp: number
}

export interface ScheduleJob {
  job_id: string
  name: string
  posts: string[]
  schedule_type: string
  schedule: string
  max_pages: number
  next_run_time: string | null
}

export interface CrawlLog {
  id: number
  post: string
  status: string
  start_time: string | null
  end_time: string | null
  total_pages: number | null
  new_records: number
  updated_records: number
  error_message: string | null
}

export interface NiukeRecord {
  id: number
  content_id: string | null
  title: string
  company: string
  post: string
  content: string
  edit_time: string | null
  read: number | null
  status: number
}

export interface NiukeDataResponse {
  data: NiukeRecord[]
  total: number
}

export interface StatsData {
  total_records: number
  active_records: number
  post_stats: Array<{ post: string; count: number }>
}

export interface CrawlRequest {
  posts: string[]
  max_pages?: number
}

export interface CreateScheduleRequest {
  posts: string[]
  schedule_type: 'cron' | 'interval'
  schedule: string
  max_pages: number
  name?: string
}

export type WSMessageType =
  | 'crawl_start'
  | 'crawl_page_done'
  | 'crawl_post_done'
  | 'crawl_all_done'
  | 'crawl_error'
  | 'job_status_change'

export interface WSMessage {
  type: WSMessageType
  data?: unknown
  message?: string
}

export interface CrawlProgress {
  post: string
  currentPage: number
  totalPages: number
  newRecords: number
  updatedRecords: number
  status: 'running' | 'done' | 'error'
  error?: string
}

export interface QuickCrawlRequest {
  posts: string[]
  max_pages: number
}

export interface ExportMdRequest {
  post?: string
  company?: string
  limit: number
  group_by?: 'company' | 'post'
}

export interface FilterOptions {
  posts: string[]
  companies: string[]
}

export interface JobPostItem {
  name: string
  jobId: number
}

export interface JobTreeChild {
  id: number
  name: string
  level: number
}

export interface JobTreeItem {
  id: number
  name: string
  level: number
  children: JobTreeChild[]
}

export type CardTheme = 'xiaohongshu' | 'bytedance' | 'alibaba' | 'minimal' | 'business'

export interface CardDraft {
  markdown: string
  theme: CardTheme
  title: string
  caption: string
  tags: string[]
}

export interface WeChatPreviewRequest {
  markdown: string
  title?: string
}

export interface WeChatPreviewData {
  title: string
  html: string
  metadata: Record<string, unknown>
}

export interface WeChatDraftRequest {
  markdown: string
  title?: string
  author?: string
  digest?: string
  content_source_url?: string
  cover_theme?: 'auto' | 'programming' | 'ai' | 'tech'
}

export interface WeChatDraftData {
  title: string
  media_id: string
  cover_media_id: string
  wechat_response?: Record<string, unknown>
}

export interface WeChatAIGenerateRequest {
  markdown: string
  title?: string
  author?: string
  digest?: string
  content_source_url?: string
  source_record_id?: number
  style?:
    | 'single_interpretation'
    | 'knowledge_deep_dive'
    | 'trend_analysis'
    | 'manual_rewrite'
    | 'quick_checklist'
    | 'interviewer_chain'
}

export interface WeChatAISaveRequest extends WeChatAIGenerateRequest {
  html: string
  title: string
  cover_prompt?: string
  cover_base64?: string
  cover_mime?: string
}

export interface WeChatArticleData {
  id: number
  source_record_id?: number | null
  title: string
  author?: string | null
  digest?: string | null
  content_source_url?: string | null
  markdown?: string | null
  html?: string | null
  cover_base64?: string | null
  cover_mime?: string | null
  prompt?: string | null
  model_info: Record<string, unknown>
  wechat_media_id?: string | null
  cover_media_id?: string | null
  status: string
  error_message?: string | null
  created_at?: string | null
  updated_at?: string | null
}

export interface WeChatQuestionAnalysisRequest {
  company: string
  post: string
  days: number
  limit?: number
}

export interface WeChatQuestionAnalysisData {
  title: string
  digest: string
  stats: {
    company: string
    post: string
    days: number
    record_count: number
    question_count: number
    unique_question_count: number
    top_questions: Array<{ question: string; count: number; category: string }>
    categories: Array<{ name: string; count: number }>
  }
  records: Array<{ id?: number; title?: string; edit_time?: string; content_id?: string; content?: string }>
}
