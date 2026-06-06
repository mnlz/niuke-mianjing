import type { NiukeRecord } from '@/api/types'

const fallback = (value: string | null | undefined, empty = '未知') => {
  const text = value?.trim()
  return text || empty
}

const escapeTableCell = (value: string | null | undefined, empty = '未知') =>
  fallback(value, empty).replace(/\|/g, '\\|').replace(/\n/g, ' ')

const normalizeInterviewContent = (value: string | null | undefined) => {
  const text = fallback(value, '暂无内容')
    .replace(/\r/g, '\n')
    .replace(/([。！？?])\s*(\d{1,2}[.、])/g, '$1\n$2')
    .replace(/([^\n])\s+(\d{1,2}[.、]\s*[^\d\s])/g, '$1\n$2')
    .replace(/\s+(?=(?:[一二三四五六七八九十]+、))/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()

  return text
    .split('\n')
    .map((line) => line.trim())
    .join('\n')
}

export const getNowcoderUrl = (record: Pick<NiukeRecord, 'content_id'>) =>
  record.content_id ? `https://www.nowcoder.com/discuss/${record.content_id}` : ''

export const buildRecordMarkdown = (record: NiukeRecord) => {
  const sourceUrl = getNowcoderUrl(record)
  const lines = [
    `# ${fallback(record.title, '无标题面经')}`,
    '',
    '| 字段 | 内容 |',
    '| --- | --- |',
    `| 公司 | ${escapeTableCell(record.company)} |`,
    `| 岗位方向 | ${escapeTableCell(record.post)} |`,
    `| 发布时间 | ${escapeTableCell(record.edit_time, '-')} |`,
  ]

  if (sourceUrl) {
    lines.push(`| 原文链接 | [牛客讨论区](${sourceUrl}) |`)
  }

  lines.push('', '## 面经正文', '', normalizeInterviewContent(record.content))
  return lines.join('\n')
}

export const summarizeMarkdown = (markdown: string, maxLength = 120) => {
  const text = markdown
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/[#>*_`|[\]()]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()

  if (text.length <= maxLength) return text
  return `${text.slice(0, maxLength)}...`
}

export const buildXhsDraft = (record: Partial<NiukeRecord> | null, markdown: string) => {
  const company = fallback(record?.company, '大厂')
  const post = fallback(record?.post, '技术岗')
  const title = `${company}${post}面经 | 这些问题高频出现`
  const summary = summarizeMarkdown(markdown)
  const sourceUrl = record?.content_id ? getNowcoderUrl(record as NiukeRecord) : ''
  const tags = Array.from(new Set(['面经', '校招', '社招', '牛客面经', company, post].filter(Boolean)))

  const caption = [
    title,
    '',
    `这篇整理了 ${company} ${post} 的面试复盘，适合面试前快速过一遍问题方向。`,
    summary ? `核心内容：${summary}` : '',
    sourceUrl ? `原文来源：${sourceUrl}` : '',
    '',
    tags.map((tag) => `#${tag}`).join(' '),
  ]
    .filter(Boolean)
    .join('\n')

  return { title, caption, tags }
}
