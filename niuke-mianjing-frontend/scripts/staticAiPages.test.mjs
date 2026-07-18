import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const pages = {
  'ai-analysis-static-home.html': ['求职竞争力雷达', '全景求职研判', '内测反馈'],
  'ai-analysis-static-create.html': ['STEP 01', 'STEP 06', '简历解析结果', '确认使用此简历'],
  'ai-analysis-static-sample-report.html': ['AI 报告示例', '综合匹配度', '面试准备清单'],
  'ai-analysis-static-reports.html': ['AI 报告中心', '搜索报告', '查看完整报告'],
}
const links = Object.keys(pages)

for (const [file, texts] of Object.entries(pages)) {
  const html = await readFile(new URL(`../public/${file}`, import.meta.url), 'utf8')
  assert.match(html, /^<!doctype html>/i, `${file} must be a complete HTML document`)
  assert.match(html, /<style>[\s\S]+<\/style>/i, `${file} must embed CSS`)
  assert.match(html, /<script>[\s\S]+<\/script>/i, `${file} must embed JavaScript`)
  for (const text of texts) assert.ok(html.includes(text), `${file} is missing ${text}`)
  for (const link of links) assert.ok(html.includes(link), `${file} is missing link to ${link}`)
  assert.doesNotMatch(html, /fetch\s*\(|axios|\/api\//, `${file} must not call an API`)
}

const currentCreate = await readFile(new URL('../../static-prototypes/ai-analysis-create-current.html', import.meta.url), 'utf8')
for (const text of ['刘子扬', '15372257175', '285625439@qq.com', '教育经历', '实习经历', '项目经历', '专业技能', '个人总结', '高级编辑']) {
  assert.ok(currentCreate.includes(text), `current prototype is missing ${text}`)
}
assert.match(currentCreate, /^<!doctype html>/i)
assert.match(currentCreate, /data-action="edit"/)
assert.match(currentCreate, /data-action="confirm"/)
assert.doesNotMatch(currentCreate, /<link[^>]+href=|<script[^>]+src=|fetch\s*\(|axios|\/api\//i)

const premiumReport = await readFile(new URL('../../static-prototypes/ai-report-premium-concept.html', import.meta.url), 'utf8')
for (const text of [
  '岗位自适应面试备战报告', '字节后端', '美团后端', '字节 Android', '面试准备度',
  '01 目标岗位考纲', '02 最近面试情报', '03 简历证据与改写', '04 个性化押题',
  '05 核心题作答框架', '06 专项实战', '07 模拟考试', '08 冲刺计划', '09 考前速查',
  '10 数据与可信度', '演示数据', '查看依据', '原始简历写法', '推荐写法', '修改合理性',
  'data-scenario="byte-backend"', 'data-scenario="meituan-backend"', 'data-scenario="byte-android"',
  'data-filter="basics"', 'data-filter="project"', 'data-answer', 'data-score', 'data-plan="3"', 'data-plan="7"', 'data-plan="14"',
]) assert.ok(premiumReport.includes(text), `premium report prototype is missing ${text}`)
assert.match(premiumReport, /^<!doctype html>/i)
assert.match(premiumReport, /@media \(max-width:/)
assert.match(premiumReport, /@media print/)
assert.doesNotMatch(premiumReport, /<link[^>]+href=|<script[^>]+src=|fetch\s*\(|axios|\/api\//i)

console.log('static AI pages tests passed')
