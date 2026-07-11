import assert from 'node:assert/strict'

const { interviewRoute } = await import('../src/pages/PublicJobs/jobUtils.ts')

assert.equal(
  interviewRoute({ id: 893, company: '阿里巴巴', post: '后端开发', title: '阿里一面', status: 1 }),
  '/interviews?record=893&company=%E9%98%BF%E9%87%8C%E5%B7%B4%E5%B7%B4&post=%E5%90%8E%E7%AB%AF%E5%BC%80%E5%8F%91',
)
