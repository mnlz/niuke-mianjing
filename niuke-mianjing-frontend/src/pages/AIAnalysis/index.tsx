import React, { useEffect, useState } from 'react'
import { ArrowRightOutlined, CheckCircleFilled, SafetyCertificateOutlined } from '@ant-design/icons'
import { Button } from 'antd'
import { useNavigate } from 'react-router-dom'
import { logApi, recruitmentApi } from '@/api'
import type { RecruitmentSource, StatsData } from '@/api/types'
import AnalysisHeader from './AnalysisHeader'
import { SAMPLE_REPORT_PATH } from './analysisUtils'
import { reportTypes } from './config'
import './style.css'

const modeCodes = ['COMPANY', 'COMPARE', 'INTERVIEW', 'RESUME', 'FULL SCAN', 'REVERSE']
const modeTags = ['公司 + 岗位', '公司 × N + 岗位', '岗位 + 面经', '岗位 + 简历', '4 元素完整报告', '简历 → 岗位库']

const AIAnalysis: React.FC = () => {
  const navigate = useNavigate()
  const [stats, setStats] = useState<StatsData | null>(null)
  const [sources, setSources] = useState<RecruitmentSource[]>([])

  useEffect(() => {
    logApi.stats().then(setStats).catch(() => setStats(null))
    recruitmentApi.sources().then(setSources).catch(() => setSources([]))
  }, [])
  const start = (reportType = 'full') => navigate(`/ai-analysis/create?report=${reportType}`)

  return (
    <div className="ai-product-page ai-landing-page">
      <AnalysisHeader active="home" />
      <main>
        <section className="ai-hero">
          <div className="ai-hero-copy">
            <div className="ai-kicker"><span /> RECRUITMENT INTELLIGENCE · V2</div>
            <h1>60 秒读懂一家公司，<br />再决定<span className="ai-title-accent">要不要投</span>。</h1>
            <p>把官方岗位、真实面经与个人简历放在同一张分析桌上，得到能直接指导投递和面试准备的判断书——而不是又一份泛泛的“建议列表”。</p>
            <div className="ai-hero-actions">
              <Button type="primary" size="large" onClick={() => start()}>
                免费生成第一份报告 <ArrowRightOutlined />
              </Button>
              <Button size="large" onClick={() => navigate(SAMPLE_REPORT_PATH)}>查看报告示例</Button>
            </div>
            <div className="ai-trust-line">
              <span><CheckCircleFilled /> 使用当前招聘数据</span>
              <span><SafetyCertificateOutlined /> 简历仅用于本次分析</span>
            </div>
          </div>

          <div className="ai-report-sample">
            <div className="sample-toolbar"><b>OfferLens Report</b><span>LIVE PREVIEW</span></div>
            <div className="sample-body">
              <small>全景求职研判</small>
              <h3>字节跳动 · 人工智能/算法</h3>
              <p>岗位要求 × 近期面经 × 个人简历</p>
              <div className="sample-score-row">
                <div><span>综合匹配度</span><strong>83<em>/100</em></strong><b>建议投递</b></div>
                <div><span>优先补强</span><strong>3<em> 项</em></strong><b className="warning">7 天可准备</b></div>
              </div>
              <div className="sample-insight">
                <span>01</span><div><b>招聘信号</b><p>目标方向仍有持续招聘需求，工程落地能力权重上升。</p></div>
              </div>
              <div className="sample-insight">
                <span>02</span><div><b>面试重点</b><p>项目深挖、模型评估与系统设计应放在准备清单前列。</p></div>
              </div>
              <div className="sample-progress"><span style={{ width: '83%' }} /></div>
              <small>示例预览 · 最终结论以实时数据和你的简历为准</small>
            </div>
          </div>
        </section>

        <section className="ai-live-strip">
          <div><strong>{stats?.total_records?.toLocaleString() || '—'}</strong><span>真实面经样本</span><small>持续更新</small></div>
          <div><strong>{stats?.active_records?.toLocaleString() || '—'}</strong><span>当前有效面经</span><small>当前可分析</small></div>
          <div><strong>{sources.length || '—'}</strong><span>招聘官网数据源</span><small>官方来源</small></div>
          <div><strong>{stats?.post_stats?.length || '—'}</strong><span>覆盖求职方向</span><small>岗位分类</small></div>
        </section>

        <section className="ai-proof-section">
          <div className="ai-section-heading">
            <span>REPORT CAPABILITY SNAPSHOT</span>
            <h2>把模糊的“我行不行”，<br />拆成看得见的能力坐标。</h2>
            <p>报告会把岗位要求、真实面经和个人经历放到同一套维度中，给出差距与行动优先级。</p>
          </div>
          <div className="ai-proof-layout">
            <article className="ai-radar-card">
              <div className="ai-proof-card-head"><div><small>CAPABILITY MATRIX</small><h3>求职竞争力雷达 · 后端开发</h3></div><span>4 元素综合</span></div>
              <div className="ai-radar-body">
                <svg viewBox="0 0 320 280" role="img" aria-label="六维求职竞争力雷达图">
                  <g className="radar-grid">
                    <polygon points="160,35 247,85 247,185 160,235 73,185 73,85" />
                    <polygon points="160,69 217,102 217,168 160,201 103,168 103,102" />
                    <polygon points="160,102 189,119 189,152 160,169 131,152 131,119" />
                    <path d="M160 35V235M73 85L247 185M247 85L73 185" />
                  </g>
                  <polygon className="radar-value" points="160,49 228,96 222,171 160,217 101,169 94,97" />
                  <g className="radar-dots">
                    <circle cx="160" cy="49" r="4" /><circle cx="228" cy="96" r="4" /><circle cx="222" cy="171" r="4" />
                    <circle cx="160" cy="217" r="4" /><circle cx="101" cy="169" r="4" /><circle cx="94" cy="97" r="4" />
                  </g>
                  <g className="radar-labels">
                    <text x="160" y="17">基础能力</text><text x="278" y="76">项目深度</text><text x="281" y="207">系统设计</text>
                    <text x="160" y="264">工程落地</text><text x="39" y="207">业务理解</text><text x="39" y="76">面试表达</text>
                  </g>
                </svg>
                <div className="ai-radar-summary"><strong>82</strong><span>综合竞争力</span><small>优势 3 项 · 优先补强 2 项</small></div>
              </div>
              <div className="ai-radar-legend"><span><i /> 当前能力</span><span><i /> 目标岗位基准</span><b>生成后按你的数据更新</b></div>
            </article>

            <div className="ai-feedback-panel">
              <div className="ai-feedback-summary"><span>内测反馈</span><strong>4.9<small>/5</small></strong><p>“最有用的不是分数，而是终于知道下一步先做什么。”</p></div>
              <article><div><b>林同学</b><span>后端开发 · 校招</span></div><em>★★★★★</em><p>岗位要求和面经放在一起后，准备顺序一下就清楚了，项目经历也知道该怎么改。</p></article>
              <article><div><b>周同学</b><span>人工智能/算法 · 实习</span></div><em>★★★★★</em><p>跨公司对比很直观，帮我把原本随缘投递的名单排出了优先级。</p></article>
              <article><div><b>陈同学</b><span>前端开发 · 社招</span></div><em>★★★★★</em><p>每个能力缺口都有对应的面试问题，不再只是拿到一份泛泛的简历建议。</p></article>
            </div>
          </div>
        </section>

        <section className="ai-scenarios-section">
          <div className="ai-section-heading row">
            <div><span>SIX ANALYSIS MODES</span><h2>四种数据，六种组合。</h2></div>
            <Button onClick={() => start('full')}>开始配置 <ArrowRightOutlined /></Button>
          </div>
          <div className="ai-scenario-grid">
            {reportTypes.map((item, index) => (
              <button key={item.value} className={item.featured ? 'featured' : ''} onClick={() => start(item.value)}>
                <span>{item.icon} // {modeCodes[index]}{item.featured && ' · 推荐'}</span>
                <h3>{item.label}</h3><p>{item.desc}</p><b>{modeTags[index]}</b><i>→</i>
              </button>
            ))}
          </div>
        </section>

        <section className="ai-final-cta">
          <div><span>READY TO START</span><h2>别再猜自己“能不能投”。<br />让数据告诉你下一步。</h2><p>四种真实数据，一份能马上执行的求职判断。</p></div>
          <Button type="primary" size="large" onClick={() => start()}>开始生成分析报告 <ArrowRightOutlined /></Button>
        </section>
      </main>
    </div>
  )
}

export default AIAnalysis
