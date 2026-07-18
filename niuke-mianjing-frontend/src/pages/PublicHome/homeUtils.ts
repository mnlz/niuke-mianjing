import type { NiukeRecord, StatsData } from '@/api/types'

export interface JobMarketSnapshot {
  sourceCount: number
  aiCompanyCount: number
  company: string
  recruitmentType: string
  totalJobs: number
  aiJobs: number
  engineeringJobs: number
}

export const featuredInterviewCompanies = ['字节跳动', '腾讯', '阿里巴巴']

export const fallbackMarketSignals = [
  {
    index: '01',
    label: 'AI Opportunity',
    metric: 'AI',
    unit: '热门岗位',
    title: 'AI 正在成为工程岗位的通用能力',
    text: '从 Agent、RAG 到 AI Infra，先看企业真实需求，再决定项目和面试准备重点。',
    action: '查看 AI 岗位',
    path: '/jobs?ai_hot=1',
    tone: 'primary',
  },
  {
    index: '02',
    label: 'Official Openings',
    metric: '15',
    unit: '家招聘官网',
    title: '先看岗位，再决定投哪里',
    text: '按统一岗位族比较不同公司的真实职责与任职要求。',
    action: '探索官网岗位',
    path: '/jobs',
    tone: 'light',
  },
  {
    index: '03',
    label: 'AI Offer Plan',
    metric: '1份',
    unit: '专属作战报告',
    title: '把岗位要求变成准备清单',
    text: '结合简历、岗位和真实面经，生成项目深挖、八股、算法题与简历修改建议。',
    action: '生成我的报告',
    path: '/ai-analysis/create?report=full',
    tone: 'accent',
  },
]

export const buildMarketSignals = (snapshot: JobMarketSnapshot | null, stats: StatsData | null) => {
  if (!snapshot) return fallbackMarketSignals

  return [
    {
      index: '01',
      label: 'AI Opportunity',
      metric: snapshot.aiJobs.toLocaleString(),
      unit: '个 AI 热门岗位',
      title: 'AI 热招已经出现，现在就看机会',
      text: `当前${snapshot.company}${snapshot.recruitmentType}覆盖 AI 算法、AI 应用/Agent 与 AI Infra。先看企业真实需求，再准备项目与面试。`,
      action: '立即查看 AI 岗位',
      path: '/jobs?source=tencent&type=campus&ai_hot=1',
      tone: 'primary',
    },
    {
      index: '02',
      label: 'Official Openings',
      metric: snapshot.totalJobs.toLocaleString(),
      unit: '个官网岗位',
      title: `${snapshot.company}${snapshot.recruitmentType}，哪些岗位值得投？`,
      text: `其中技术大类 ${snapshot.engineeringJobs.toLocaleString()} 个，职责与任职要求均可追溯到招聘官网。`,
      action: '按岗位族筛选',
      path: '/jobs?source=tencent&type=campus',
      tone: 'light',
    },
    {
      index: '03',
      label: 'AI Offer Plan',
      metric: snapshot.sourceCount.toLocaleString(),
      unit: `家官网 · ${snapshot.aiCompanyCount} 家 AI 公司`,
      title: '别只收藏岗位，把它变成 Offer 计划',
      text: `结合 ${stats?.total_records?.toLocaleString() || '-'} 篇真实面经和个人简历，生成项目深挖、八股、算法题与简历修改建议。`,
      action: '生成我的面试报告',
      path: '/ai-analysis/create?report=full',
      tone: 'accent',
    },
  ]
}

export const pickFeaturedInterviews = (groups: NiukeRecord[][]) =>
  groups
    .map((records) => records.find((item) => item.company && item.company !== '未知公司' && item.content?.length > 80))
    .filter(Boolean) as NiukeRecord[]
