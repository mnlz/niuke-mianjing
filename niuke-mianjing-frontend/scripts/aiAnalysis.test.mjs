import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const {
  buildAnalysisRequest,
  extractResumeContacts,
  filterReports,
  generationBlocker,
  resumeRequirementError,
  SAMPLE_REPORT_PATH,
  toggleInterviewId,
} = await import('../src/pages/AIAnalysis/analysisUtils.ts')

const baseConfig = {
  reportType: 'full',
  source: 'bytedance',
  company: '字节跳动',
  compareSources: ['bytedance', 'tencent'],
  recruitmentType: 'campus',
  track: 'ai',
  trackName: '人工智能/算法',
  interviewIds: [9, 3],
  resume: 'LLM 项目经历',
}

assert.deepEqual(buildAnalysisRequest(baseConfig), {
  report_type: 'full',
  source: 'bytedance',
  recruitment_type: 'campus',
  track: 'ai',
  selected_interview_ids: [9, 3],
  resume: 'LLM 项目经历',
})
assert.equal('model' in buildAnalysisRequest(baseConfig), false)

assert.deepEqual(buildAnalysisRequest({ ...baseConfig, reportType: 'company_compare' }), {
  report_type: 'company_compare',
  source: 'bytedance',
  recruitment_type: 'campus',
  track: 'ai',
  compare_sources: ['bytedance', 'tencent'],
})

const record = {
  report_code: 'RPT-TEST', title: '字节跳动 · 人工智能/算法', company: '字节跳动',
  track: 'ai', track_name: '人工智能/算法', recruitment_type: 'campus', report_type: 'full',
  content: '# 匹配结论', model: 'gpt-test', created_at: '2026-07-10T12:00:00.000Z', updated_at: null,
}

assert.deepEqual(filterReports([record], '字节', 'all'), [record])
assert.deepEqual(filterReports([record], '腾讯', 'all'), [])
assert.deepEqual(filterReports([record], '', 'job'), [])
assert.deepEqual(filterReports([record], '', 'full'), [record])
assert.deepEqual(toggleInterviewId([1, 2], 3, true), [1, 2, 3])
assert.deepEqual(toggleInterviewId([1, 2, 3, 4, 5, 6, 7, 8], 9, true), [1, 2, 3, 4, 5, 6, 7, 8])
assert.deepEqual(toggleInterviewId([1, 2, 3], 2, false), [1, 3])
assert.equal(SAMPLE_REPORT_PATH, '/ai-analysis/sample-report')
assert.equal(generationBlocker(false, '请先上传简历'), 'login')
assert.equal(generationBlocker(true, '请先上传简历'), '请先上传简历')
assert.equal(generationBlocker(true, ''), '')

assert.deepEqual(extractResumeContacts('邮箱：candidate@example.com 手机：138 0013 8000'), {
  email: 'candidate@example.com',
  phone: '13800138000',
})
assert.deepEqual(extractResumeContacts('暂无联系方式'), { email: '', phone: '' })
assert.equal(resumeRequirementError(true, '', false), '请先上传或粘贴简历')
assert.equal(resumeRequirementError(true, '项目经历', false), '请确认简历解析结果')
assert.equal(resumeRequirementError(true, '项目经历', true), '')
assert.equal(resumeRequirementError(false, '', false), '')

const configSource = await readFile(new URL('../src/pages/AIAnalysis/config.ts', import.meta.url), 'utf8')
assert.match(configSource, /全景求职研判/)
assert.doesNotMatch(configSource, /四合一作战地图/)

const headerSource = await readFile(new URL('../src/pages/AIAnalysis/AnalysisHeader.tsx', import.meta.url), 'utf8')
const homeSource = await readFile(new URL('../src/pages/AIAnalysis/index.tsx', import.meta.url), 'utf8')
const createSource = await readFile(new URL('../src/pages/AIAnalysis/CreatePage.tsx', import.meta.url), 'utf8')
const sampleSource = await readFile(new URL('../src/pages/AIAnalysis/SampleReportPage.tsx', import.meta.url), 'utf8')
const reportsSource = await readFile(new URL('../src/pages/AIAnalysis/ReportsPage.tsx', import.meta.url), 'utf8')
const styleSource = await readFile(new URL('../src/pages/AIAnalysis/style.css', import.meta.url), 'utf8')
const recruitmentApiSource = await readFile(new URL('../src/api/recruitment.ts', import.meta.url), 'utf8')
const apiTypesSource = await readFile(new URL('../src/api/types.ts', import.meta.url), 'utf8')

assert.match(headerSource, /AI · v2/)
assert.match(headerSource, /ai-header-primary-nav/)
assert.match(headerSource, /ai-header-account/)
assert.match(headerSource, /ai-header-mobile-nav/)
assert.match(headerSource, /aria-label="AI 分析"/)
assert.match(headerSource, /aria-label="我的报告"/)
assert.match(createSource, /const TOTAL_STEPS = 7/)
assert.match(createSource, /gpt-5\.4-mini/)
assert.match(createSource, /gpt-5\.5/)
assert.match(createSource, /gpt-5\.6-sol/)
assert.match(createSource, /预览配置/)
assert.match(createSource, /ParsedResume/)
assert.match(createSource, /简历内容（可编辑）/)
assert.match(createSource, /ai-resume-section-tags/)
assert.doesNotMatch(createSource, /上传时识别结果/)
assert.match(createSource, /parsedResume\.page_count/)
assert.match(createSource, /parsedResume\.sections/)
assert.match(createSource, /最大 8 MB/)
assert.doesNotMatch(createSource, /ai-step-keyboard/)
assert.doesNotMatch(createSource, /addEventListener\('keydown'/)
assert.match(createSource, /aria-current=/)
assert.match(createSource, /aria-pressed=/)
assert.match(createSource, /FULL SCAN/)
assert.match(sampleSource, /RPT-SAMPLE-0711/)
assert.match(sampleSource, /示例面经统计/)
assert.match(sampleSource, /出现 5 次/)
assert.match(sampleSource, /命中率 83%/)
assert.match(reportsSource, /REPORT WORKSPACE/)
assert.match(reportsSource, /最近更新/)
assert.match(reportsSource, /ai-report-drawer-cover/)
assert.doesNotMatch(reportsSource, /DATA OWNERSHIP/)
assert.match(reportsSource, /aria-label="查看报告"/)
assert.match(reportsSource, /aria-label="下载报告"/)
assert.match(reportsSource, /aria-label="删除报告"/)
assert.match(styleSource, /\.ai-report-kpis \{[\s\S]*?grid-template-columns: repeat\(3, 1fr\);/)
assert.match(recruitmentApiSource, /ApiResponse<ParsedResume>/)
assert.match(apiTypesSource, /interface ParsedResumeSection/)
assert.match(styleSource, /\.ai-scenarios-section::before \{ inset: 0; \}/)
assert.match(styleSource, /\.user-session-actions \.ant-btn > span:not\(\.ant-btn-icon\)/)
for (const protectedCopy of ['全景求职研判', '字节跳动 · 人工智能\/算法', '>83<', '招聘信号', '面试重点']) {
  assert.ok(homeSource.includes(protectedCopy), `protected home preview is missing ${protectedCopy}`)
}

console.log('aiAnalysis tests passed')
