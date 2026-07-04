import { recruitmentTypeName, recruitmentTypeOptions } from '@/constants/recruitment'

export const reportTypes = [
  { label: '岗位分析', value: 'job', desc: '聚合岗位要求，拆解能力画像' },
  { label: '公司横向对比', value: 'company_compare', desc: '对比不同公司的招聘侧重点' },
  { label: '岗位 + 面经', value: 'job_interviews', desc: '结合最近面经定位面试考点' },
  { label: '岗位 + 面经 + 简历', value: 'full', desc: '输出完整求职匹配报告' },
] as const

export type ReportType = typeof reportTypes[number]['value']

export const recruitmentTypes = recruitmentTypeOptions
export { recruitmentTypeName }
