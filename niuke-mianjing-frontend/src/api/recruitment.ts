import client from './client'
import type {
  ApiResponse,
  ParsedResume,
  RecruitmentAIReportResult,
  RecruitmentAIReportRecord,
  RecruitmentInterview,
  RecruitmentJobPage,
  RecruitmentRefreshResult,
  RecruitmentSource,
  RecruitmentTrack,
  RecruitmentType,
  RecruitmentVersion,
} from './types'

export const recruitmentApi = {
  sources: () =>
    client.get<ApiResponse<RecruitmentSource[]>>('/api/recruitment/sources').then((r) => r.data.data),

  tracks: () =>
    client.get<ApiResponse<RecruitmentTrack[]>>('/api/recruitment/tracks').then((r) => r.data.data),

  recruitmentTypes: () =>
    client.get<ApiResponse<Array<{ id: RecruitmentType; name: string }>>>('/api/recruitment/recruitment-types').then((r) => r.data.data),

  jobs: (params: { source: string; keyword?: string; track?: string; recruitment_type?: RecruitmentType; page?: number; page_size?: number }) =>
    client.get<ApiResponse<RecruitmentJobPage>>('/api/recruitment/jobs', { params, timeout: 60000 }).then((r) => r.data.data),

  versions: () =>
    client.get<ApiResponse<RecruitmentVersion[]>>('/api/recruitment/versions').then((r) => r.data.data),

  refresh: (data: { source?: string; recruitment_type?: RecruitmentType | 'all'; max_pages?: number }) =>
    client.post<ApiResponse<RecruitmentRefreshResult>>('/api/recruitment/refresh', data, { timeout: 10 * 60 * 1000 }).then((r) => r.data.data),

  interviews: (params: { source: string; recruitment_type: RecruitmentType; source_job_id: string; limit?: number }) =>
    client.get<ApiResponse<RecruitmentInterview[]>>('/api/recruitment/job-interviews', { params }).then((r) => r.data.data),

  trackInterviews: (params: { source: string; recruitment_type: RecruitmentType; track: string; limit?: number }) =>
    client.get<ApiResponse<RecruitmentInterview[]>>('/api/recruitment/track-interviews', { params }).then((r) => r.data.data),

  aiReport: (data: { report_type: 'job' | 'company_compare' | 'job_interviews' | 'resume_job' | 'full' | 'resume_match'; source?: string; recruitment_type?: RecruitmentType; source_job_id?: string; track?: string; company?: string; resume?: string; compare_sources?: string[]; selected_interview_ids?: number[] }) =>
    client.post<ApiResponse<RecruitmentAIReportResult>>('/api/recruitment/ai-report', data, { timeout: 120000 }).then((r) => r.data.data),

  aiReports: () =>
    client.get<ApiResponse<RecruitmentAIReportRecord[]>>('/api/recruitment/ai-reports').then((r) => r.data.data),

  aiReportDetail: (reportCode: string) =>
    client.get<ApiResponse<RecruitmentAIReportRecord>>(`/api/recruitment/ai-reports/${encodeURIComponent(reportCode)}`).then((r) => r.data.data),

  deleteAIReport: (reportCode: string) =>
    client.delete<ApiResponse<{ report_code: string }>>(`/api/recruitment/ai-reports/${encodeURIComponent(reportCode)}`).then((r) => r.data.data),

  parseResume: (file: File) => {
    const form = new FormData()
    form.append('file', file)
    return client.post<ApiResponse<ParsedResume>>('/api/recruitment/resume/parse', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 60000,
    }).then((r) => r.data.data)
  },
}
