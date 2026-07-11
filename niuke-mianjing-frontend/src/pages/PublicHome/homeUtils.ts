import type { NiukeRecord, StatsData } from '@/api/types'

export const featuredInterviewCompanies = ['字节跳动', '腾讯', '阿里巴巴']

export const fallbackMarketSignals = [
  {
    index: '01',
    label: 'AI Engineering',
    title: 'AI 正在成为工程岗位的通用能力',
    text: '从 Agent、RAG 到智能化研发工具，大模型能力正在进入后端、客户端与基础架构岗位。',
    trend: '持续升温',
  },
  {
    index: '02',
    label: 'Infrastructure',
    title: '基础架构仍然决定工程上限',
    text: '分布式系统、性能、稳定性和云原生，依然是大厂技术岗位反复强调的底层能力。',
    trend: '长期高频',
  },
  {
    index: '03',
    label: 'Real Experience',
    title: '项目深度，比技术名词更重要',
    text: '岗位和面试都在关注真实规模、方案取舍、效果指标，以及你到底解决了什么问题。',
    trend: '核心信号',
  },
]

export const buildMarketSignals = (stats: StatsData | null) => {
  const posts = [...(stats?.post_stats || [])].sort((a, b) => b.count - a.count)
  if (!stats?.total_records || posts.length < 2) return fallbackMarketSignals

  const first = posts[0]
  const second = posts[1]
  const firstRatio = Math.round((first.count / stats.total_records) * 100)
  const secondRatio = Math.round((second.count / stats.total_records) * 100)

  return [
    {
      index: '01',
      label: 'Top Track',
      title: `${first.post}是当前面经主战场`,
      text: `本地库已有 ${first.count.toLocaleString()} 篇真实面经来自${first.post}，约占全部样本 ${firstRatio}%。`,
      trend: '样本最高',
    },
    {
      index: '02',
      label: 'Runner-up',
      title: `${second.post}保持高频出现`,
      text: `${second.post}当前有 ${second.count.toLocaleString()} 篇真实面经，约占全部样本 ${secondRatio}%，适合作为第二复习重点。`,
      trend: '高频方向',
    },
    {
      index: '03',
      label: 'Live Dataset',
      title: '首页信号来自当前数据库',
      text: `这些判断基于本地 ${stats.total_records.toLocaleString()} 篇真实面经统计，数据更新后这里会同步变化。`,
      trend: '实时更新',
    },
  ]
}

export const pickFeaturedInterviews = (groups: NiukeRecord[][]) =>
  groups
    .map((records) => records.find((item) => item.company && item.company !== '未知公司' && item.content?.length > 80))
    .filter(Boolean) as NiukeRecord[]
