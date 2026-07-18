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

const signals = buildMarketSignals({
  sourceCount: 15,
  aiCompanyCount: 4,
  company: '腾讯',
  recruitmentType: '校招',
  totalJobs: 82,
  aiJobs: 12,
  engineeringJobs: 33,
}, stats)

assert.equal(signals.length, 3)
assert.equal(signals[0].title, 'AI 热招已经出现，现在就看机会')
assert.equal(signals[0].metric, '12')
assert.match(signals[1].text, /技术大类 33 个/)
assert.match(signals[2].text, /1,098 篇真实面经/)
assert.equal(signals[2].path, '/ai-analysis/create?report=full')

assert.equal(buildMarketSignals(null, stats)[0].title, 'AI 正在成为工程岗位的通用能力')
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
