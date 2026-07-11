import assert from 'node:assert/strict'

const { buildRecordMarkdown } = await import('../src/utils/markdown.ts')

const markdown = buildRecordMarkdown({
  id: 1,
  content_id: '123',
  title: '腾讯后端一面',
  company: '腾讯',
  post: '后端开发',
  content: '1. 自我介绍 2. Redis 怎么用？',
  edit_time: '2026-07-06T11:35:21',
  read: 0,
  status: 1,
})

assert.match(markdown, /腾讯后端一面/)
assert.match(markdown, /2026-07-06 11:35/)
assert.doesNotMatch(markdown, /\| 字段 \| 内容 \|/)
assert.doesNotMatch(markdown, /nowcoder|牛客讨论区/)
