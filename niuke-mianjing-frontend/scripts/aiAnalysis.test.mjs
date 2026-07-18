import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const {
  buildAnalysisRequest,
  extractResumeContacts,
  filterReports,
  generationBlocker,
  replaceFirstText,
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
  sourceJobId: 'job-42',
  interviewIds: [9, 3],
  resume: 'LLM 项目经历',
  modelId: 42,
}

assert.deepEqual(buildAnalysisRequest(baseConfig), {
  report_type: 'full',
  source: 'bytedance',
  recruitment_type: 'campus',
  track: 'ai',
  source_job_id: 'job-42',
  selected_interview_ids: [9, 3],
  resume: 'LLM 项目经历',
  model_id: 42,
})
assert.equal(buildAnalysisRequest(baseConfig).model_id, 42)

assert.deepEqual(buildAnalysisRequest({ ...baseConfig, reportType: 'company_compare' }), {
  report_type: 'company_compare',
  source: 'bytedance',
  recruitment_type: 'campus',
  track: 'ai',
  compare_sources: ['bytedance', 'tencent'],
  model_id: 42,
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
assert.deepEqual(toggleInterviewId([1, 2, 3, 4, 5, 6, 7, 8], 9, true), [1, 2, 3, 4, 5, 6, 7, 8, 9])
assert.deepEqual(toggleInterviewId([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 13, true), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
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
assert.equal(replaceFirstText('项目 A\n项目 A', '项目 A', '项目 $1'), '项目 $1\n项目 A')
assert.equal(replaceFirstText('项目 A', '不存在', '项目 B'), '项目 A')

const configSource = await readFile(new URL('../src/pages/AIAnalysis/config.ts', import.meta.url), 'utf8')
assert.match(configSource, /个性化面试手册/)
assert.doesNotMatch(configSource, /四合一作战地图/)

const headerSource = await readFile(new URL('../src/pages/AIAnalysis/AnalysisHeader.tsx', import.meta.url), 'utf8')
const userSessionSource = await readFile(new URL('../src/components/UserSessionButton/index.tsx', import.meta.url), 'utf8')
const homeSource = await readFile(new URL('../src/pages/AIAnalysis/index.tsx', import.meta.url), 'utf8')
const createSource = await readFile(new URL('../src/pages/AIAnalysis/CreatePage.tsx', import.meta.url), 'utf8')
const resumeEditorSource = await readFile(new URL('../src/pages/AIAnalysis/ResumeEditor.tsx', import.meta.url), 'utf8')
const sampleSource = await readFile(new URL('../src/pages/AIAnalysis/SampleReportPage.tsx', import.meta.url), 'utf8')
const reportsSource = await readFile(new URL('../src/pages/AIAnalysis/ReportsPage.tsx', import.meta.url), 'utf8')
const styleSource = await readFile(new URL('../src/pages/AIAnalysis/style.css', import.meta.url), 'utf8')
const recruitmentApiSource = await readFile(new URL('../src/api/recruitment.ts', import.meta.url), 'utf8')
const apiTypesSource = await readFile(new URL('../src/api/types.ts', import.meta.url), 'utf8')
const aiModelsSource = await readFile(new URL('../src/pages/AIModels/index.tsx', import.meta.url), 'utf8')
const aiModelStyleSource = await readFile(new URL('../src/pages/AIModels/style.css', import.meta.url), 'utf8')
const appSource = await readFile(new URL('../src/App.tsx', import.meta.url), 'utf8')
const layoutSource = await readFile(new URL('../src/components/Layout/index.tsx', import.meta.url), 'utf8')

assert.doesNotMatch(headerSource, /AI · v2/)
assert.doesNotMatch(headerSource, /ai-version-tag/)
assert.doesNotMatch(userSessionSource, /UserOutlined/)
assert.match(headerSource, /ai-header-primary-nav/)
assert.match(headerSource, /ai-header-account/)
assert.match(headerSource, /ai-header-mobile-nav/)
assert.match(headerSource, /aria-label="AI 分析"/)
assert.match(headerSource, /aria-label="我的报告"/)
assert.match(headerSource, /新建分析/)
assert.match(headerSource, /报告示例/)
assert.match(headerSource, /\/ai-analysis\/sample-report/)
assert.match(headerSource, /ai-header-report-cta/)
assert.match(headerSource, /ai-header-nav-item/)
assert.match(userSessionSource, /Dropdown/)
assert.match(userSessionSource, /ai-account-pill/)
assert.match(userSessionSource, /ai-account-avatar/)
assert.match(createSource, /const TOTAL_STEPS = 7/)
assert.doesNotMatch(createSource, /mockModels/)
assert.match(createSource, /recruitmentApi\.aiModels/)
assert.match(createSource, /is_default/)
assert.doesNotMatch(createSource, /实际生成仍使用系统当前配置的模型/)
assert.match(createSource, /ParsedResume/)
assert.match(createSource, /<ResumeEditor/)
assert.match(createSource, /ai-horizontal-steps/)
assert.match(createSource, /确认你的简历内容/)
assert.match(createSource, /ai-resume-file-row/)
assert.match(createSource, /ai-live-preview/)
assert.match(createSource, /previewItems\.slice\(0, step\)/)
for (const previewLabel of ['分析场景', '目标公司', '目标岗位', '面经样本', '个人简历', '分析模型', '生成确认']) {
  assert.ok(createSource.includes(previewLabel), `create preview is missing ${previewLabel}`)
}
assert.match(createSource, /parsedResume\?\.name/)
assert.match(createSource, /parsedResume\?\.sections\.length/)
assert.doesNotMatch(createSource, /上传时识别结果/)
assert.match(createSource, /parsedResume\?\.page_count/)
assert.match(createSource, /最大 8 MB/)
assert.match(createSource, /URL\.createObjectURL/)
assert.match(createSource, /URL\.revokeObjectURL/)
assert.match(createSource, /预览简历/)
assert.match(createSource, /ai-resume-preview-frame/)
assert.match(resumeEditorSource, /基本信息/)
assert.match(resumeEditorSource, /ai-resume-section-card/)
assert.match(resumeEditorSource, /ai-resume-section-tabs/)
assert.match(resumeEditorSource, /activeSection/)
assert.match(resumeEditorSource, /高级编辑/)
assert.match(resumeEditorSource, /replaceFirstText/)
assert.match(resumeEditorSource, /parsedResume\.sections/)
assert.doesNotMatch(resumeEditorSource, /ai-resume-avatar/)
assert.doesNotMatch(createSource, /ai-step-keyboard/)
assert.doesNotMatch(createSource, /addEventListener\('keydown'/)
assert.match(createSource, /aria-current=/)
assert.match(createSource, /aria-pressed=/)
assert.match(createSource, /FULL SCAN/)
assert.match(createSource, /投递的具体岗位/)
assert.match(createSource, /recruitmentApi\.interviews/)
assert.match(createSource, /sourceJobId: selectedJobId/)
assert.match(createSource, /最多 12 篇/)
for (const sampleCopy of ['RPT-SAMPLE-0713', '面试核心资料', '本场必看', '近期高频题', '项目拷打地图', '简历触发八股', '最可能的算法题', '简历修改建议', '附录：次优先级追问']) {
  assert.ok(sampleSource.includes(sampleCopy), `sample report is missing ${sampleCopy}`)
}
for (const removedCopy of ['岗位选择与投递优先级', '面试准备度', '7-DAY OFFER SPRINT', '模拟面试达标线']) {
  assert.ok(!sampleSource.includes(removedCopy), `sample report still contains ${removedCopy}`)
}
assert.doesNotMatch(sampleSource, /命中率/)
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
assert.match(recruitmentApiSource, /adminAIModels/)
assert.match(recruitmentApiSource, /testAIModel/)
assert.match(aiModelsSource, /api_key_masked/)
assert.match(aiModelsSource, /连接测试/)
assert.match(aiModelsSource, /forceRender/)
assert.doesNotMatch(aiModelsSource, /destroyOnClose/)
assert.match(aiModelsSource, /form\.resetFields\(\)/)
assert.match(aiModelsSource, /rowKey="id"/)
assert.match(aiModelsSource, /channel_name/)
assert.match(recruitmentApiSource, /model_id/)
assert.match(createSource, /selectedModelId/)
assert.match(createSource, /channel_name/)
assert.match(aiModelsSource, /title: '模型',[\s\S]*?width: 140/)
assert.match(aiModelsSource, /title: 'Endpoint',[\s\S]*?width: 360/)
assert.doesNotMatch(aiModelsSource, /title: 'Endpoint',[^\n]*ellipsis/)
assert.match(aiModelsSource, /scroll=\{\{ x: 1060 \}\}/)
assert.match(aiModelStyleSource, /\.ai-model-endpoint \{ white-space: nowrap; \}/)
assert.match(appSource, /path="\/ai-models"/)
assert.match(layoutSource, /AI 模型/)
assert.match(styleSource, /\.ai-scenarios-section::before \{ inset: 0; \}/)
assert.match(styleSource, /\.ai-account-pill\.ant-btn/)
assert.match(styleSource, /\.ai-header-primary-nav \.ant-btn \{[\s\S]*?font-size: 13px;/)
assert.match(styleSource, /\.ai-resume-section-copy \{[\s\S]*?max-height: 360px;[\s\S]*?overflow: auto;/)
assert.doesNotMatch(styleSource, /\.ai-resume-section-copy \{[^}]*min-height:/)
assert.match(styleSource, /\.ai-resume-section-copy p \{[^}]*font-size: 13px;/)
assert.match(styleSource, /\.ai-resume-drop \.anticon \{[^}]*margin-right: 12px;/)
assert.match(styleSource, /\.ai-resume-drop b \{[^}]*margin-right: 8px;/)
assert.match(styleSource, /\.ai-resume-section-tabs b \{[^}]*font-size: 12px;/)
assert.match(styleSource, /\.ai-resume-section-tabs i \{[^}]*font: 10px/)
assert.match(styleSource, /\.ai-resume-section-tabs small \{[^}]*font-size: 10px;/)
assert.match(styleSource, /\.ai-resume-section-card header b \{[^}]*font-size: 13px;/)
assert.match(styleSource, /\.ai-resume-section-card header \.ant-btn \{[^}]*font-size: 12px;/)
assert.match(styleSource, /\.ai-resume-section-card textarea\.ant-input \{[^}]*font-size: 13px;/)
for (const protectedCopy of ['全景求职研判', '字节跳动 · 人工智能\/算法', '>83<', '招聘信号', '面试重点']) {
  assert.ok(homeSource.includes(protectedCopy), `protected home preview is missing ${protectedCopy}`)
}

console.log('aiAnalysis tests passed')
