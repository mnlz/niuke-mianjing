import assert from 'node:assert/strict'

const { buildMarketSignals, featuredInterviewCompanies, pickFeaturedInterviews } = await import('../src/pages/PublicHome/homeUtils.ts')

const stats = {
  total_records: 1098,
  active_records: 875,
  post_stats: [
    { post: '后端开发', count: 420 },
    { post: '前端开发', count: 210 },
    { post: '人工智能/算法', count: 88 },
  ],
}

const signals = buildMarketSignals(stats)

assert.equal(signals.length, 3)
assert.equal(signals[0].title, '后端开发是当前面经主战场')
assert.match(signals[0].text, /420 篇真实面经/)
assert.match(signals[1].text, /19%/)
assert.match(signals[2].text, /1,098 篇/)

assert.equal(buildMarketSignals(null)[0].title, 'AI 正在成为工程岗位的通用能力')
assert.deepEqual(featuredInterviewCompanies, ['字节跳动', '腾讯', '阿里巴巴'])

const makeRecord = (id, company, content) => ({
  id,
  content_id: String(id),
  title: `${company}面经`,
  company,
  post: '后端开发',
  content,
  edit_time: null,
  read: 0,
  status: 1,
})

assert.deepEqual(
  pickFeaturedInterviews([
    [makeRecord(1, '字节跳动', '短'), makeRecord(2, '字节跳动', '足够长的真实面经内容'.repeat(12))],
    [makeRecord(3, '腾讯', '足够长的真实面经内容'.repeat(12))],
    [makeRecord(4, '阿里巴巴', '足够长的真实面经内容'.repeat(12))],
  ]).map((item) => item.company),
  ['字节跳动', '腾讯', '阿里巴巴'],
)
