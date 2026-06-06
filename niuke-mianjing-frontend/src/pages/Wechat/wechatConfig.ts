export type SourceMode = 'single' | 'analysis' | 'manual'
export type GenerateMode = 'html' | 'markdown'
export type ContentType =
  | 'single_interpretation'
  | 'knowledge_deep_dive'
  | 'trend_analysis'
  | 'manual_rewrite'
  | 'quick_checklist'
  | 'interviewer_chain'

export const contentTypeOptions: Array<{ label: string; value: ContentType }> = [
  { label: '单篇面经解读', value: 'single_interpretation' },
  { label: '技术知识点精讲', value: 'knowledge_deep_dive' },
  { label: '面试趋势分析', value: 'trend_analysis' },
  { label: '手动粘贴', value: 'manual_rewrite' },
  { label: '高频题速查清单', value: 'quick_checklist' },
  { label: '面试官追问链路', value: 'interviewer_chain' },
]

export const contentTypeGuides: Record<ContentType, { title: string; text: string; button: string }> = {
  single_interpretation: {
    title: '单篇面经解读',
    text: '选择一篇真实面经，拆解面试过程、问题难度、考点和复习建议。',
    button: '生成单篇解读',
  },
  knowledge_deep_dive: {
    title: '技术知识点精讲',
    text: '从一篇面经里挑 3-5 个重要知识点展开，讲原理、问法和常见追问。',
    button: '生成知识点精讲',
  },
  trend_analysis: {
    title: '面试趋势分析',
    text: '按公司、岗位和时间范围分析多篇面经，输出高频题和备考优先级。',
    button: '分析趋势并生成',
  },
  manual_rewrite: {
    title: '手动粘贴',
    text: '自由粘贴 Markdown 或草稿，由 AI 改写成公众号文章。',
    button: '按粘贴内容生成',
  },
  quick_checklist: {
    title: '高频题速查清单',
    text: '按公司和岗位抽取多篇真实面经，整理成适合收藏的速查清单。',
    button: '生成速查清单',
  },
  interviewer_chain: {
    title: '面试官追问链路',
    text: '从核心问题出发，还原面试官可能怎么追问、候选人怎么接。',
    button: '生成追问链路',
  },
}

export const analysisRangeOptions = [
  { label: '最近 7 天', value: 7 },
  { label: '最近 30 天', value: 30 },
  { label: '最近 90 天', value: 90 },
]

export const defaultMarkdown = '# 面经标题\n\n请选择一条面经，或在这里粘贴 Markdown 内容。'

export const getSourceMode = (contentType: ContentType): SourceMode => {
  if (contentType === 'trend_analysis' || contentType === 'quick_checklist') return 'analysis'
  if (contentType === 'manual_rewrite') return 'manual'
  return 'single'
}
