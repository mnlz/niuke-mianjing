import React from 'react'
import { Button, message, Tag } from 'antd'
import { ArrowRightOutlined, CopyOutlined, PrinterOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import AnalysisHeader from './AnalysisHeader'
import './style.css'

const SampleReportPage: React.FC = () => {
  const navigate = useNavigate()
  const copySummary = async () => {
    await navigator.clipboard.writeText('腾讯后端开发全景求职研判：综合匹配度 86，建议投递；优先补强系统设计、项目证据和故障复盘。')
    message.success('报告摘要已复制')
  }

  return (
    <div className="ai-product-page ai-reports-page">
      <AnalysisHeader active="home" />
      <main>
        <div className="ai-reports-title ai-sample-title">
          <div><span>PUBLIC SAMPLE · READ-ONLY</span><h1>AI 报告示例</h1><p>固定演示样本，展示 OfferLens 正式报告的完整结构与呈现能力。</p></div>
          <div className="ai-sample-tools"><Button icon={<CopyOutlined />} onClick={copySummary}>复制摘要</Button><Button icon={<PrinterOutlined />} onClick={() => window.print()}>打印 / PDF</Button><Button type="primary" onClick={() => navigate('/ai-analysis/create')}>生成我的报告 <ArrowRightOutlined /></Button></div>
        </div>

        <article className="ai-sample-report-v2">
          <section className="ai-sample-cover">
            <div><small>RPT-SAMPLE-0711 · 全景求职研判</small><h2>腾讯后端开发求职分析报告</h2><p>腾讯 · 后端开发 · 校招　|　生成于 2026-07-11</p><div><Tag>6 · 官方岗位</Tag><Tag>8 · 近期面经</Tag><Tag>1 · 个人简历</Tag><Tag>v2.3 · 分析模型</Tag></div></div>
            <div className="ai-score-ring"><strong>86</strong><span>综合匹配</span><small>建议投递</small></div>
          </section>

          <section className="ai-sample-metrics"><div><small>POSITIONS</small><strong>6</strong><span>官方岗位样本</span></div><div><small>INTERVIEWS</small><strong>8</strong><span>近 60 天面经</span></div><div><small>STRENGTHS</small><strong>4</strong><span>核心优势维度</span></div><div><small>GAPS</small><strong>3</strong><span>优先补强项</span></div></section>

          <section className="ai-sample-section"><header><i>01</i><h3>核心判断</h3><span>CORE VERDICT</span></header><div className="ai-sample-grid"><article className="good"><Tag color="green">建议投递</Tag><h4>基础能力与项目方向高度吻合</h4><p>系统设计证据补强后，目标岗位竞争力会明显提升。</p></article><article><Tag color="blue">招聘信号</Tag><h4>工程落地能力权重持续上升</h4><p>云原生、性能优化和 AI 工程落地在近期岗位中出现频率更高。</p></article></div></section>

          <section className="ai-sample-section"><header><i>02</i><h3>能力矩阵</h3><span>CAPABILITY MATRIX</span></header><div className="ai-sample-radar"><svg viewBox="0 0 320 290" aria-label="六维能力雷达图"><g className="radar-grid"><polygon points="160,25 272,90 272,210 160,275 48,210 48,90"/><polygon points="160,68 235,111 235,189 160,232 85,189 85,111"/><path d="M160 25V275M48 90L272 210M272 90L48 210"/></g><polygon className="radar-value" points="160,44 246,103 230,193 160,248 76,196 75,105"/><text x="160" y="154" textAnchor="middle" className="radar-center-num">86</text><text x="160" y="174" textAnchor="middle" className="radar-center-lab">综合匹配</text></svg><div className="ai-sample-bars">{[['编程基础',92],['系统设计',72],['项目证据',64],['面试表达',81],['工程规范',78],['软素质',85]].map(([name, score]) => <div key={name}><span>{name}</span><i><b style={{ width: `${score}%` }} /></i><strong>{score}</strong></div>)}</div></div></section>

          <section className="ai-sample-section"><header><i>03</i><h3>岗位要求 × 简历证据</h3><span>JD × RESUME EVIDENCE</span></header><div className="ai-sample-table-wrap"><table><thead><tr><th>岗位要求</th><th>岗位出现频次</th><th>简历证据</th><th>判断</th><th>权重</th></tr></thead><tbody><tr><td>Java / Go 与服务端基础</td><td>6 / 6</td><td>订单系统、缓存优化</td><td><Tag color="green">强匹配</Tag></td><td>.28</td></tr><tr><td>高并发与稳定性治理</td><td>5 / 6</td><td>有方案，缺少量化指标</td><td><Tag color="gold">需补强</Tag></td><td>.24</td></tr><tr><td>系统设计与架构取舍</td><td>4 / 6</td><td>证据强度中等</td><td><Tag color="gold">需补强</Tag></td><td>.20</td></tr><tr><td>AI 工程落地</td><td>2 / 6</td><td>暂无直接证据</td><td><Tag color="red">缺失</Tag></td><td>.12</td></tr></tbody></table></div></section>

          <section className="ai-sample-section"><header><i>04</i><h3>简历改写建议</h3><span>RESUME REWRITE</span></header><div className="ai-resume-diff"><article className="before"><small>BEFORE</small><p>负责订单接口性能优化，使用 Redis 缓存，提升了系统性能。</p></article><article className="after"><small>AFTER</small><p>重构订单热点缓存与降级链路，将 P99 延迟从 180ms 降至 72ms，高峰期 QPS 提升 46%。</p></article></div></section>

          <section className="ai-sample-section"><header><i>05</i><h3>面试准备</h3><span>INTERVIEW PREP</span></header><div className="ai-sample-grid"><article><h4>高频追问</h4><ol className="ai-question-list"><li><b>Q1</b><span>缓存一致性如何保证？延迟双删的边界是什么？<small>示例面经统计 · 出现 5 次 · 命中率 83%</small></span></li><li><b>Q2</b><span>如何定位一次线上慢请求？<small>示例面经统计 · 出现 4 次 · 命中率 75%</small></span></li><li><b>Q3</b><span>为什么选择当前分库分表策略？<small>示例面经统计 · 出现 4 次 · 命中率 62%</small></span></li></ol></article><article><h4>准备顺序</h4><ol><li>项目指标与个人贡献</li><li>缓存、数据库与网络基础</li><li>系统设计和故障复盘</li><li>两轮公司专项模拟面试</li></ol></article></div></section>

          <section className="ai-action-plan"><header><div><small>06 · ACTION PLAN</small><h3>7 天冲刺计划</h3><p>按天拆解，每一步都可以直接执行。</p></div><span>EST · 6.5H / DAY</span></header><ol><li><b>DAY 1–2</b><span>补全两个核心项目的 QPS、延迟、可用性和影响面指标</span><em>4H</em></li><li><b>DAY 3</b><span>完成缓存、数据库、网络专项复习并整理笔记</span><em>6H</em></li><li><b>DAY 4–5</b><span>完成两个系统设计案例与一次故障复盘</span><em>10H</em></li><li><b>DAY 6–7</b><span>完成两轮模拟面试，回放并标注表达卡点</span><em>6H</em></li></ol></section>
        </article>
      </main>
    </div>
  )
}

export default SampleReportPage
