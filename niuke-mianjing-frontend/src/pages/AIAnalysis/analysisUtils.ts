import type { RecruitmentType } from '@/api/types'

export const SAMPLE_REPORT_PATH = '/ai-analysis/sample-report'
export const generationBlocker = (loggedIn: boolean, configError: string) => loggedIn ? configError : 'login'
export const extractResumeContacts = (text: string) => {
  const email = text.match(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/)?.[0] || ''
  const phone = text.match(/(?:\+?86[\s-]?)?1[3-9](?:[\s-]?\d){9}/)?.[0].replace(/(?:\+?86)|[\s-]/g, '') || ''
  return { email, phone }
}
export const replaceFirstText = (source: string, previous: string, next: string) => {
  const index = previous ? source.indexOf(previous) : -1
  return index < 0 ? source : `${source.slice(0, index)}${next}${source.slice(index + previous.length)}`
}
export const resumeRequirementError = (required: boolean, text: string, confirmed: boolean) => {
  if (!required) return ''
  if (!text.trim()) return '请先上传或粘贴简历'
  return confirmed ? '' : '请确认简历解析结果'
}

export type AnalysisReportType =
  | 'job'
  | 'company_compare'
  | 'job_interviews'
  | 'resume_job'
  | 'full'
  | 'resume_match'

export interface AnalysisConfig {
  reportType: AnalysisReportType
  source: string
  company: string
  compareSources: string[]
  recruitmentType: RecruitmentType
  track: string
  trackName: string
  sourceJobId?: string
  interviewIds: number[]
  resume: string
  modelId: number
}

export interface AnalysisReportRecord {
  report_code: string
  title: string
  company: string
  track: string
  track_name: string
  recruitment_type: RecruitmentType
  report_type: AnalysisReportType
  content: string
  model: string
  created_at: string
  updated_at?: string | null
}

export const buildAnalysisRequest = (config: AnalysisConfig) => {
  const request: {
    report_type: AnalysisReportType
    source: string
    recruitment_type: RecruitmentType
    track: string
    model_id: number
    source_job_id?: string
    compare_sources?: string[]
    selected_interview_ids?: number[]
    resume?: string
  } = {
    report_type: config.reportType,
    source: config.source,
    recruitment_type: config.recruitmentType,
    track: config.track,
    model_id: config.modelId,
  }

  if (config.reportType === 'company_compare' || config.reportType === 'resume_match') {
    request.compare_sources = config.compareSources
  } else if (config.sourceJobId) {
    request.source_job_id = config.sourceJobId
  }
  if (config.reportType === 'job_interviews' || config.reportType === 'full') {
    request.selected_interview_ids = config.interviewIds
  }
  if (config.reportType === 'resume_job' || config.reportType === 'full' || config.reportType === 'resume_match') {
    request.resume = config.resume
  }
  return request
}

export const filterReports = (
  reports: AnalysisReportRecord[],
  query: string,
  type: AnalysisReportType | 'all',
) => {
  const keyword = query.trim().toLowerCase()
  return reports.filter((report) => {
    const typeMatched = type === 'all' || report.report_type === type
    const queryMatched = !keyword || `${report.title} ${report.company} ${report.track_name}`.toLowerCase().includes(keyword)
    return typeMatched && queryMatched
  })
}

export const toggleInterviewId = (current: number[], id: number, checked: boolean, max = 12) => {
  if (!checked) return current.filter((item) => item !== id)
  if (current.includes(id) || current.length >= max) return current
  return [...current, id]
}
