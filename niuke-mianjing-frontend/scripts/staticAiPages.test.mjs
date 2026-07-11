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

console.log('static AI pages tests passed')
