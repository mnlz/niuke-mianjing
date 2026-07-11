import type { NiukeRecord } from '@/api/types'

type ReviewCardSource = Pick<NiukeRecord, 'content'> | null

export const normalizeInterviewText = (content: string) =>
  content
    .replace(/\r/g, '\n')
    .replace(/([。！？?])\s*(\d{1,2}[.、])/g, '$1\n$2')
    .replace(/([^\n])\s+(\d{1,2}[.、]\s*[^\d\s])/g, '$1\n$2')

export const extractReviewCards = (record: ReviewCardSource) => {
  if (!record?.content) return []
  const lines = normalizeInterviewText(record.content)
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)

  const questionLike = lines.filter((line) =>
    /(\?|？|什么|如何|怎么|区别|原理|介绍|讲讲|说说|实现|场景|为什么)/.test(line),
  )

  const source = questionLike.length > 0 ? questionLike : lines
  return source.slice(0, 8).map((line, index) => ({
    title: line.replace(/^\d{1,2}[.、]\s*/, '').slice(0, 72),
    tag: index < 3 ? '高优先级' : index < 6 ? '重点回看' : '补充',
  }))
}

export const filterRecordsByKeyword = (records: NiukeRecord[], keyword: string) => {
  const value = keyword.trim().toLowerCase()
  if (!value) return records
  return records.filter((record) =>
    `${record.title} ${record.company} ${record.post} ${record.content}`.toLowerCase().includes(value),
  )
}
