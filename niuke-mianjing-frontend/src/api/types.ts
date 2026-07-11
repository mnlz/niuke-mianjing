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
  status?: 'active' | 'paused' | 'invalid'
}

export interface ScheduleRun {
  id: number
  job_id: string
  started_at: string | null
  finished_at: string | null
  duration_seconds: number | null
  status: string
  result?: Record<string, unknown> | null
  error_message?: string | null
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

export type ReviewMastery = 'new' | 'learning' | 'fuzzy' | 'mastered'

export interface ReviewProgress {
  record_id: number
  favorite: boolean
  mastery: ReviewMastery
  note?: string | null
  last_reviewed_at?: string | null
  updated_at?: string | null
}

export interface ReviewOverview {
  company: string
  post: string
  days: number
  record_count: number
  question_count: number
  top_questions: Array<{ question: string; count: number; category: string }>
  categories: Array<{ name: string; count: number }>
  sample_records: Array<{ id: number; title: string; edit_time?: string | null; read?: number | null }>
  empty: boolean
}

export interface ReviewAIQuestion {
  question: string
  answer: string
  followups?: string[]
  tags?: string[]
}

export interface ReviewAIContent {
  summary: string
  difficulty: string
  priority: string
  questions: ReviewAIQuestion[]
  knowledge_points: Array<{ name: string; why: string; review_tip: string }>
  action_plan: string[]
}

export interface ReviewAIResult {
  record_id: number
  review: ReviewAIContent
  model?: string
  updated_at?: string | null
  cached?: boolean
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

export interface RecruitmentSource {
  source: string
  company: string
  description: string
  logo?: string
  supported_recruitment_types?: RecruitmentType[]
}

export type RecruitmentType = 'campus' | 'intern' | 'social'

export interface RecruitmentTrack {
  id: string
  name: string
  description: string
  keywords: string[]
}

export interface RecruitmentJob {
  source: string
  source_job_id: string
  company: string
  title: string
  category?: string | null
  job_family?: string | null
  inferred_track?: string | null
  inferred_track_name?: string | null
  display_category?: string | null
  location?: string | null
  country?: string | null
  business_unit?: string | null
  product?: string | null
  recruitment_type?: RecruitmentType
  employment_type?: string | null
  experience?: string | null
  description: string
  requirements: string
  highlights?: string
  preferred_qualifications?: string
  source_url: string
  updated_at?: string | null
  crawled_at: string
}

export interface RecruitmentJobPage {
  source: string
  company: string
  track?: string | null
  recruitment_type?: RecruitmentType
  keywords?: string[]
  items: RecruitmentJob[]
  page: number
  page_size: number
  total: number
  has_more: boolean
  cached: boolean
}

export interface RecruitmentVersion {
  source: string
  recruitment_type: RecruitmentType
  refresh_version?: string | null
  job_count: number
  refresh_started_at?: string | null
  synced_at?: string | null
}

export interface RecruitmentRefreshResult {
  refresh_version: string
  started_at: string
  total_jobs: number
  results: Array<{
    source: string
    recruitment_type: RecruitmentType
    status: 'success' | 'failed'
    job_count: number
    error?: string
  }>
}

export interface RecruitmentInterview {
  id: number
  content_id?: string | null
  title: string
  edit_time?: string | null
  read?: number | null
  post?: string | null
  company: string
  status: number
}

export interface ParsedResumeSection {
  key: string
  title: string
  content: string
}

export interface ParsedResume {
  text: string
  name: string
  phone: string
  email: string
  page_count: number
  char_count: number
  sections: ParsedResumeSection[]
}

export interface RecruitmentAIReportRecord {
  report_code: string
  title: string
  report_type: 'job' | 'company_compare' | 'job_interviews' | 'resume_job' | 'full' | 'resume_match'
  company: string
  track: string
  track_name: string
  recruitment_type: RecruitmentType
  content: string
  model: string
  created_at: string
  updated_at?: string | null
}

export interface RecruitmentAIReportResult extends RecruitmentAIReportRecord {
  report: string
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
  wechat_theme?: string
}

export interface WeChatPreviewData {
  title: string
  html: string
  metadata: Record<string, unknown>
}

export interface WeChatThemeItem {
  id: string
  name: string
  description?: string
}

export interface WeChatThemeGroup {
  label: string
  themes: WeChatThemeItem[]
}

export interface WeChatDraftRequest {
  markdown: string
  title?: string
  author?: string
  digest?: string
  content_source_url?: string
  cover_theme?: 'auto' | 'programming' | 'ai' | 'tech'
  wechat_theme?: string
}

export interface WeChatDraftData {
  title: string
  media_id: string
  cover_media_id: string
  wechat_response?: Record<string, unknown>
}

export interface WeChatNewspicDraftRequest {
  title: string
  content?: string
  images: string[]
  image_mimes?: string[]
  need_open_comment?: number
  only_fans_can_comment?: number
}

export interface WeChatNewspicDraftData {
  title: string
  media_id: string
  image_media_ids: string[]
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
  wechat_theme?: string
}

export interface WeChatAISaveRequest extends WeChatAIGenerateRequest {
  html: string
  title: string
  cover_prompt?: string
  cover_base64?: string
  cover_mime?: string
}

export interface WeChatCoverGenerateRequest {
  markdown: string
  title: string
  style?: WeChatAIGenerateRequest['style']
  cover_prompt?: string
}

export interface WeChatCoverGenerateData {
  cover_base64: string
  cover_mime: string
  cover_prompt: string
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
  wechat_theme?: string
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
