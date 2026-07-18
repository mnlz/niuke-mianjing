import { recruitmentTypeName, recruitmentTypeOptions } from '@/constants/recruitment'
import type { AnalysisReportType } from './analysisUtils'

export const reportTypes = [
  { label: '公司招聘动态', short: '公司分析', value: 'job', desc: '拆解目标公司近期岗位分布、职责与能力要求', icon: '01' },
  { label: '跨公司岗位对标', short: '岗位对标', value: 'company_compare', desc: '比较同一岗位在不同公司的招聘侧重点', icon: '02' },
  { label: '面试高频问题', short: '面试分析', value: 'job_interviews', desc: '把岗位要求和近期真实面经对应起来', icon: '03' },
  { label: '简历岗位诊断', short: '简历诊断', value: 'resume_job', desc: '结合公司岗位要求诊断简历匹配度', icon: '04' },
  { label: '个性化面试手册', short: '面试手册', value: 'full', desc: '用精确岗位、近期面经和简历生成项目拷打、八股与算法资料', icon: '05', featured: true },
  { label: '简历反向匹配', short: '反向匹配', value: 'resume_match', desc: '从多家公司中找出更值得优先投递的方向', icon: '06' },
] satisfies Array<{
  label: string
  short: string
  value: AnalysisReportType
  desc: string
  icon: string
  featured?: boolean
}>

export type ReportType = AnalysisReportType

export const reportTypeMeta = (value: ReportType) => reportTypes.find((item) => item.value === value) || reportTypes[0]

export const needsInterviews = (value: ReportType) => value === 'job_interviews' || value === 'full'
export const needsResume = (value: ReportType) => value === 'resume_job' || value === 'full' || value === 'resume_match'
export const isCompanyCompare = (value: ReportType) => value === 'company_compare' || value === 'resume_match'

export const recruitmentTypes = recruitmentTypeOptions
export { recruitmentTypeName }
