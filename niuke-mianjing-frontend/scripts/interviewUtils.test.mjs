import assert from 'node:assert/strict'

const { extractReviewCards, filterRecordsByKeyword } = await import('../src/pages/PublicInterviews/interviewUtils.ts')

const record = {
  id: 1,
  title: '腾讯后端一面',
  company: '腾讯',
  post: '后端开发',
  content: '1. Java 线程池原理是什么？2. Redis 如何实现缓存击穿保护？ 普通经历介绍。',
}

const cards = extractReviewCards(record)
assert.equal(cards.length, 2)
assert.equal(cards[0].title, 'Java 线程池原理是什么？')
assert.equal(cards[0].tag, '高优先级')

const records = [
  record,
  { ...record, id: 2, title: '美团测试', company: '美团', post: '测试', content: '自动化测试' },
]

assert.deepEqual(filterRecordsByKeyword(records, ' redis ').map((item) => item.id), [1])
assert.deepEqual(filterRecordsByKeyword(records, '').map((item) => item.id), [1, 2])
